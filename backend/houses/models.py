from django.db import models
from django.conf import settings
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


class Device(models.Model):
    """Device/equipment in a house (heaters, fans, lights, etc.)"""
    DEVICE_TYPES = [
        ('heater', 'Heater'),
        ('tunnel_fan', 'Tunnel Fan'),
        ('exhaust_fan', 'Exhaust Fan'),
        ('stir_fan', 'Stir Fan'),
        ('cooling_pad', 'Cooling Pad'),
        ('light', 'Light'),
        ('feeder', 'Feeder'),
        ('auger', 'Auger'),
        ('water_system', 'Water System'),
        ('ventilation', 'Ventilation'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('on', 'On'),
        ('off', 'Off'),
        ('error', 'Error'),
        ('maintenance', 'Maintenance'),
    ]
    
    house = models.ForeignKey(House, on_delete=models.CASCADE, related_name='devices')
    device_type = models.CharField(max_length=50, choices=DEVICE_TYPES)
    device_number = models.IntegerField(help_text="Device number/identifier within the house")
    name = models.CharField(max_length=200, blank=True, help_text="Optional device name")
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='off')
    percentage = models.FloatField(null=True, blank=True, help_text="Percentage/level (0-100) for variable devices")
    
    # Metadata
    last_update = models.DateTimeField(auto_now=True)
    last_checked = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        unique_together = ['house', 'device_type', 'device_number']
        ordering = ['house', 'device_type', 'device_number']
        indexes = [
            models.Index(fields=['house', 'device_type']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.house} - {self.get_device_type_display()} #{self.device_number}"


class ControlSettings(models.Model):
    """Control settings for a house (temperature curves, ventilation, etc.)"""
    house = models.OneToOneField(House, on_delete=models.CASCADE, related_name='control_settings')
    
    # Temperature settings
    temperature_curve = models.JSONField(
        default=dict,
        help_text="Day-based temperature targets {day: temperature}"
    )
    min_temperature = models.FloatField(null=True, blank=True, help_text="Minimum temperature (F)")
    max_temperature = models.FloatField(null=True, blank=True, help_text="Maximum temperature (F)")
    target_temperature = models.FloatField(null=True, blank=True, help_text="Current target temperature (F)")
    temperature_offset = models.FloatField(default=0.0, help_text="Temperature offset adjustment")
    
    # Humidity settings
    humidity_target = models.FloatField(null=True, blank=True, help_text="Target humidity percentage")
    humidity_treatment_enabled = models.BooleanField(default=False)
    humidity_min = models.FloatField(null=True, blank=True)
    humidity_max = models.FloatField(null=True, blank=True)
    
    # CO2 settings
    co2_target = models.FloatField(null=True, blank=True, help_text="Target CO2 level (ppm)")
    co2_treatment_enabled = models.BooleanField(default=False)
    co2_max = models.FloatField(null=True, blank=True)
    
    # Ventilation settings
    ventilation_mode = models.CharField(
        max_length=50,
        default='minimum',
        choices=[
            ('minimum', 'Minimum Ventilation'),
            ('tunnel', 'Tunnel Ventilation'),
            ('natural', 'Natural Ventilation'),
            ('mixed', 'Mixed Mode'),
        ]
    )
    static_pressure_target = models.FloatField(null=True, blank=True, help_text="Target static pressure")
    static_pressure_min = models.FloatField(null=True, blank=True)
    static_pressure_max = models.FloatField(null=True, blank=True)
    
    # Lighting settings
    lighting_schedule = models.JSONField(
        default=dict,
        help_text="Lighting schedule configuration"
    )
    light_dimmer_level = models.FloatField(null=True, blank=True, help_text="Light dimmer percentage (0-100)")
    
    # Cooling pad settings
    cooling_pad_enabled = models.BooleanField(default=False)
    cooling_pad_threshold = models.FloatField(null=True, blank=True)
    
    # Fogger settings
    fogger_enabled = models.BooleanField(default=False)
    fogger_threshold = models.FloatField(null=True, blank=True)
    
    # Water & Feed settings
    water_on_demand_enabled = models.BooleanField(default=True)
    feed_schedule = models.JSONField(default=dict, help_text="Feed schedule configuration")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Control Settings"
        verbose_name_plural = "Control Settings"
    
    def __str__(self):
        return f"Control Settings - {self.house}"


class HouseConfiguration(models.Model):
    """System configuration for a house"""
    house = models.OneToOneField(House, on_delete=models.CASCADE, related_name='configuration')
    
    # Dimensions
    length_feet = models.FloatField(null=True, blank=True, help_text="House length in feet")
    width_feet = models.FloatField(null=True, blank=True, help_text="House width in feet")
    height_feet = models.FloatField(null=True, blank=True, help_text="House height in feet")
    total_square_feet = models.FloatField(null=True, blank=True, help_text="Total square footage")
    
    # Sensor layout
    sensor_layout = models.JSONField(default=dict, help_text="Sensor positions and types")
    
    # Relay layout
    relay_layout = models.JSONField(default=dict, help_text="Relay assignments and configurations")
    
    # Fan capacity
    fan_air_capacity_cfm = models.FloatField(null=True, blank=True, help_text="Total fan air capacity in CFM")
    tunnel_fan_count = models.IntegerField(default=0)
    exhaust_fan_count = models.IntegerField(default=0)
    stir_fan_count = models.IntegerField(default=0)
    
    # Scale settings
    scale_settings = models.JSONField(default=dict, help_text="Scale configuration")
    
    # Equipment layout
    silo_count = models.IntegerField(default=0)
    auger_count = models.IntegerField(default=0)
    feeder_count = models.IntegerField(default=0)
    drinker_count = models.IntegerField(default=0)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "House Configuration"
        verbose_name_plural = "House Configurations"
    
    def __str__(self):
        return f"Configuration - {self.house}"
    
    def save(self, *args, **kwargs):
        # Auto-calculate total square feet
        if self.length_feet and self.width_feet:
            self.total_square_feet = self.length_feet * self.width_feet
        super().save(*args, **kwargs)


class Sensor(models.Model):
    """Sensor information for a house"""
    SENSOR_TYPES = [
        ('temperature', 'Temperature'),
        ('humidity', 'Humidity'),
        ('pressure', 'Pressure'),
        ('co2', 'CO2'),
        ('ammonia', 'Ammonia'),
        ('wind_speed', 'Wind Speed'),
        ('wind_direction', 'Wind Direction'),
        ('water_meter', 'Water Meter'),
        ('feed_scale', 'Feed Scale'),
        ('bird_scale', 'Bird Scale'),
        ('other', 'Other'),
    ]
    
    house = models.ForeignKey(House, on_delete=models.CASCADE, related_name='sensors')
    sensor_type = models.CharField(max_length=50, choices=SENSOR_TYPES)
    sensor_number = models.IntegerField(help_text="Sensor number/identifier")
    location = models.CharField(max_length=200, blank=True, help_text="Sensor location description")
    
    # Calibration
    calibration_data = models.JSONField(default=dict, help_text="Calibration parameters")
    last_calibration = models.DateTimeField(null=True, blank=True)
    calibration_due_date = models.DateField(null=True, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['house', 'sensor_type', 'sensor_number']
        ordering = ['house', 'sensor_type', 'sensor_number']
    
    def __str__(self):
        return f"{self.house} - {self.get_sensor_type_display()} #{self.sensor_number}"


class TemperatureCurve(models.Model):
    """Day-based temperature curve for a house"""
    control_settings = models.ForeignKey(
        ControlSettings,
        on_delete=models.CASCADE,
        related_name='temperature_curves'
    )
    day = models.IntegerField(help_text="Day of flock (0-42)")
    target_temperature = models.FloatField(help_text="Target temperature in Fahrenheit")
    notes = models.TextField(blank=True)
    
    class Meta:
        unique_together = ['control_settings', 'day']
        ordering = ['day']
    
    def __str__(self):
        return f"Day {self.day}: {self.target_temperature}°F"


class DeviceStatus(models.Model):
    """Historical device status records"""
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='status_history')
    status = models.CharField(max_length=20)
    percentage = models.FloatField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['device', '-timestamp']),
            models.Index(fields=['timestamp']),
        ]
    
    def __str__(self):
        return f"{self.device} - {self.status} at {self.timestamp}"


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


class WaterConsumptionAlert(models.Model):
    """Alert for abnormal water consumption detected"""
    SEVERITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    house = models.ForeignKey(House, on_delete=models.CASCADE, related_name='water_alerts')
    farm = models.ForeignKey('farms.Farm', on_delete=models.CASCADE, related_name='water_alerts')
    
    # Alert details
    alert_date = models.DateField(help_text="Date when the abnormal consumption was detected")
    growth_day = models.IntegerField(null=True, blank=True, help_text="Growth day when alert occurred")
    current_consumption = models.FloatField(help_text="Current water consumption (L/day)")
    baseline_consumption = models.FloatField(help_text="Baseline/average consumption (L/day)")
    expected_consumption = models.FloatField(
        null=True, 
        blank=True, 
        help_text="Age-adjusted expected consumption (L/day) based on growth day and bird count"
    )
    increase_percentage = models.FloatField(help_text="Percentage increase from baseline")
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='medium')
    
    # Alert metadata
    message = models.TextField(help_text="Alert message describing the anomaly")
    detection_method = models.CharField(
        max_length=50,
        default='statistical',
        help_text="Method used to detect anomaly (statistical, threshold, ml)"
    )
    
    # Status
    is_acknowledged = models.BooleanField(default=False)
    acknowledged_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='acknowledged_water_alerts'
    )
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    
    # Email notification
    email_sent = models.BooleanField(default=False)
    email_sent_at = models.DateTimeField(null=True, blank=True)
    email_recipients = models.JSONField(
        default=list,
        help_text="List of email addresses that received the alert"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['house', '-created_at']),
            models.Index(fields=['farm', '-created_at']),
            models.Index(fields=['is_acknowledged', '-created_at']),
            models.Index(fields=['severity', '-created_at']),
            models.Index(fields=['alert_date', '-created_at']),
        ]
        verbose_name = "Water Consumption Alert"
        verbose_name_plural = "Water Consumption Alerts"
        # Prevent duplicate alerts for the same house on the same date
        unique_together = ['house', 'alert_date']
    
    def __str__(self):
        return f"Water Alert - House {self.house.house_number} ({self.severity}) - {self.alert_date}"
    
    def acknowledge(self, user=None):
        """Mark alert as acknowledged"""
        from django.utils import timezone
        self.is_acknowledged = True
        self.acknowledged_at = timezone.now()
        if user:
            self.acknowledged_by = user
        self.save()
