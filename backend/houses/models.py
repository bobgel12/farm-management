from django.db import models
from django.utils import timezone
from datetime import timedelta
from farms.models import Farm


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
