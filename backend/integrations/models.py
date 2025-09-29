from django.db import models
from django.utils import timezone
from farms.models import Farm


class IntegrationLog(models.Model):
    """Log integration activities and status"""
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='integration_logs')
    integration_type = models.CharField(max_length=50, help_text="Type of integration (rotem, future_system, etc.)")
    action = models.CharField(max_length=100, help_text="Action performed (sync, test_connection, etc.)")
    status = models.CharField(
        max_length=20,
        choices=[
            ('success', 'Success'),
            ('failed', 'Failed'),
            ('partial', 'Partial Success'),
            ('in_progress', 'In Progress'),
        ],
        help_text="Status of the action"
    )
    message = models.TextField(blank=True, help_text="Additional details or error message")
    data_points_processed = models.IntegerField(default=0, help_text="Number of data points processed")
    execution_time = models.FloatField(null=True, blank=True, help_text="Execution time in seconds")
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['farm', 'integration_type']),
            models.Index(fields=['timestamp']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.farm.name} - {self.integration_type} - {self.action} ({self.status})"


class IntegrationError(models.Model):
    """Track integration errors and their resolution"""
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='integration_errors')
    integration_type = models.CharField(max_length=50, help_text="Type of integration")
    error_type = models.CharField(max_length=100, help_text="Type of error (connection, authentication, data, etc.)")
    error_message = models.TextField(help_text="Detailed error message")
    error_code = models.CharField(max_length=50, blank=True, help_text="Error code if available")
    stack_trace = models.TextField(blank=True, help_text="Stack trace for debugging")
    resolved = models.BooleanField(default=False, help_text="Whether the error has been resolved")
    resolution_notes = models.TextField(blank=True, help_text="Notes about how the error was resolved")
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.CharField(max_length=100, blank=True, help_text="Who resolved the error")
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['farm', 'integration_type']),
            models.Index(fields=['resolved']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.farm.name} - {self.error_type} ({'Resolved' if self.resolved else 'Open'})"
    
    def resolve(self, resolved_by="", notes=""):
        """Mark error as resolved"""
        self.resolved = True
        self.resolved_at = timezone.now()
        self.resolved_by = resolved_by
        self.resolution_notes = notes
        self.save()


class IntegrationHealth(models.Model):
    """Track integration health metrics"""
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='integration_health')
    integration_type = models.CharField(max_length=50)
    is_healthy = models.BooleanField(default=True, help_text="Whether the integration is currently healthy")
    last_successful_sync = models.DateTimeField(null=True, blank=True)
    last_attempted_sync = models.DateTimeField(null=True, blank=True)
    consecutive_failures = models.IntegerField(default=0, help_text="Number of consecutive failures")
    success_rate_24h = models.FloatField(default=0.0, help_text="Success rate in the last 24 hours")
    average_response_time = models.FloatField(null=True, blank=True, help_text="Average response time in seconds")
    last_error = models.ForeignKey(
        IntegrationError, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        help_text="Last error encountered"
    )
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['farm', 'integration_type']
        ordering = ['-updated_at']
    
    def __str__(self):
        status = "Healthy" if self.is_healthy else "Unhealthy"
        return f"{self.farm.name} - {self.integration_type} ({status})"