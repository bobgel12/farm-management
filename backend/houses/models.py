from django.db import models
from django.utils import timezone
from datetime import timedelta
from farms.models import Farm
import json


class House(models.Model):
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='houses')
    house_number = models.IntegerField()
    capacity = models.IntegerField(default=1000, help_text="Maximum chicken capacity")
    chicken_in_date = models.DateField()
    chicken_out_date = models.DateField(null=True, blank=True)
    chicken_out_day = models.IntegerField(default=40)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Integration fields
    is_integrated = models.BooleanField(default=False, help_text="Whether this house is integrated with external system")
    system_house_id = models.CharField(max_length=100, null=True, blank=True, help_text="External system house ID")
    last_system_sync = models.DateTimeField(null=True, blank=True, help_text="Last sync with external system")
    
    # Age tracking (for both integrated and non-integrated)
    current_age_days = models.IntegerField(default=0, help_text="Current chicken age in days")
    batch_start_date = models.DateField(null=True, blank=True, help_text="Date when current batch started")
    expected_harvest_date = models.DateField(null=True, blank=True, help_text="Expected harvest date")

    class Meta:
        unique_together = ['farm', 'house_number']
        ordering = ['farm', 'house_number']

    def __str__(self):
        return f"{self.farm.name} - House {self.house_number}"

    @property
    def current_day(self):
        """Calculate current chicken age in days (day 0 = first day chickens are in)"""
        if not self.chicken_in_date:
            return None
        
        # Use timezone-aware date calculation to ensure consistency
        today = timezone.now().date()
        if self.chicken_out_date and today > self.chicken_out_date:
            return None  # House is empty
        
        # Calculate days since chicken in date, where day 0 is the first day
        # This ensures that if chickens arrive on day X, then on day X it's day 0
        days_since_in = (today - self.chicken_in_date).days
        return days_since_in
    
    @property
    def age_days(self):
        """Get current age in days - use current_age_days if set, otherwise calculate from dates"""
        if self.current_age_days > 0:
            return self.current_age_days
        return self.current_day or 0

    @property
    def days_remaining(self):
        """Calculate days remaining until chicken out"""
        if not self.chicken_in_date or not self.chicken_out_date:
            return None
        
        today = timezone.now().date()
        if today > self.chicken_out_date:
            return 0
        
        return (self.chicken_out_date - today).days

    @property
    def status(self):
        """Get current house status"""
        if not self.is_active:
            return 'inactive'
        
        if not self.chicken_in_date:
            return 'empty'
        
        current_day = self.current_day
        if current_day is None:
            return 'empty'
        
        if current_day < 0:
            return 'setup'
        elif current_day == 0:
            return 'arrival'
        elif current_day <= 7:
            return 'early_care'
        elif current_day <= 14:
            return 'growth'
        elif current_day <= 21:
            return 'maturation'
        elif current_day <= 35:
            return 'production'
        elif current_day <= 40:
            return 'pre_exit'
        else:
            return 'cleanup'

    def save(self, *args, **kwargs):
        # Auto-calculate chicken_out_date if not provided
        if self.chicken_in_date and not self.chicken_out_date:
            self.chicken_out_date = self.chicken_in_date + timedelta(days=self.chicken_out_day)
        super().save(*args, **kwargs)
    
    def get_latest_snapshot(self):
        """Get the latest monitoring snapshot for this house"""
        return self.monitoring_snapshots.order_by('-timestamp').first()
    
    def get_snapshots_for_range(self, start_date, end_date):
        """Get monitoring snapshots for a date range"""
        return self.monitoring_snapshots.filter(
            timestamp__gte=start_date,
            timestamp__lte=end_date
        ).order_by('timestamp')
    
    def get_stats(self, days=7):
        """Calculate statistics for the last N days"""
        from django.utils import timezone
        from django.db.models import Avg, Max, Min
        
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        snapshots = self.monitoring_snapshots.filter(
            timestamp__gte=start_date,
            timestamp__lte=end_date
        )
        
        if not snapshots.exists():
            return None
        
        # Extract metrics from JSON field
        stats = {
            'temperature': {
                'avg': snapshots.aggregate(Avg('average_temperature'))['average_temperature__avg'],
                'max': snapshots.aggregate(Max('average_temperature'))['average_temperature__max'],
                'min': snapshots.aggregate(Min('average_temperature'))['average_temperature__min'],
            },
            'humidity': {
                'avg': snapshots.aggregate(Avg('humidity'))['humidity__avg'],
                'max': snapshots.aggregate(Max('humidity'))['humidity__max'],
                'min': snapshots.aggregate(Min('humidity'))['humidity__min'],
            },
            'pressure': {
                'avg': snapshots.aggregate(Avg('static_pressure'))['static_pressure__avg'],
                'max': snapshots.aggregate(Max('static_pressure'))['static_pressure__max'],
                'min': snapshots.aggregate(Min('static_pressure'))['static_pressure__min'],
            },
            'total_snapshots': snapshots.count(),
            'period_days': days
        }
        
        return stats


class HouseMonitoringSnapshot(models.Model):
    """Comprehensive snapshot of house monitoring data at a specific time"""
    house = models.ForeignKey(House, on_delete=models.CASCADE, related_name='monitoring_snapshots')
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    
    # Key metrics (extracted from JSON for easier querying)
    average_temperature = models.FloatField(null=True, blank=True)
    outside_temperature = models.FloatField(null=True, blank=True)
    humidity = models.FloatField(null=True, blank=True)
    static_pressure = models.FloatField(null=True, blank=True)
    target_temperature = models.FloatField(null=True, blank=True)
    ventilation_level = models.FloatField(null=True, blank=True)
    
    # Growth and bird info
    growth_day = models.IntegerField(null=True, blank=True)
    bird_count = models.IntegerField(null=True, blank=True)
    livability = models.FloatField(null=True, blank=True)
    
    # Consumption
    water_consumption = models.FloatField(null=True, blank=True)
    feed_consumption = models.FloatField(null=True, blank=True)
    
    # Airflow
    airflow_cfm = models.FloatField(null=True, blank=True)
    airflow_percentage = models.FloatField(null=True, blank=True)
    
    # Status indicators
    connection_status = models.IntegerField(null=True, blank=True, help_text="0=disconnected, 1=connected")
    alarm_status = models.CharField(max_length=20, default='normal', choices=[
        ('normal', 'Normal'),
        ('warning', 'Warning'),
        ('critical', 'Critical'),
    ])
    
    # Raw data as JSON for flexibility
    raw_data = models.JSONField(default=dict, help_text="Complete raw data from Rotem API")
    sensor_data = models.JSONField(default=dict, help_text="Structured sensor data (temp sensors, etc.)")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['house', '-timestamp']),
            models.Index(fields=['timestamp']),
            models.Index(fields=['house', 'alarm_status', '-timestamp']),
        ]
        verbose_name = "House Monitoring Snapshot"
        verbose_name_plural = "House Monitoring Snapshots"
    
    def __str__(self):
        return f"{self.house} - {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
    
    @property
    def has_alarms(self):
        """Check if snapshot has active alarms"""
        return self.alarm_status != 'normal'
    
    @property
    def is_connected(self):
        """Check if house is connected"""
        return self.connection_status == 1


class HouseAlarm(models.Model):
    """Alarm information from monitoring snapshots"""
    ALARM_SEVERITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    ALARM_TYPE_CHOICES = [
        ('temperature', 'Temperature'),
        ('humidity', 'Humidity'),
        ('pressure', 'Pressure'),
        ('connection', 'Connection'),
        ('consumption', 'Consumption'),
        ('equipment', 'Equipment'),
        ('other', 'Other'),
    ]
    
    snapshot = models.ForeignKey(HouseMonitoringSnapshot, on_delete=models.CASCADE, related_name='alarms', null=True, blank=True)
    house = models.ForeignKey(House, on_delete=models.CASCADE, related_name='alarms')
    
    alarm_type = models.CharField(max_length=50, choices=ALARM_TYPE_CHOICES)
    severity = models.CharField(max_length=20, choices=ALARM_SEVERITY_CHOICES, default='medium')
    message = models.TextField()
    
    # Alarm metadata
    parameter_name = models.CharField(max_length=100, null=True, blank=True)
    parameter_value = models.FloatField(null=True, blank=True)
    threshold_value = models.FloatField(null=True, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.CharField(max_length=100, null=True, blank=True)
    
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['house', '-timestamp']),
            models.Index(fields=['is_active', '-timestamp']),
            models.Index(fields=['severity', '-timestamp']),
        ]
        verbose_name = "House Alarm"
        verbose_name_plural = "House Alarms"
    
    def __str__(self):
        return f"{self.house} - {self.alarm_type} ({self.severity}) - {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
    
    def resolve(self, resolved_by='system'):
        """Mark alarm as resolved"""
        from django.utils import timezone
        self.is_resolved = True
        self.is_active = False
        self.resolved_at = timezone.now()
        self.resolved_by = resolved_by
        self.save()
