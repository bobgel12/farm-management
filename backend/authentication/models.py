"""
Authentication models for password reset and security
"""
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.crypto import get_random_string
import uuid


class PasswordResetToken(models.Model):
    """Model for storing password reset tokens"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_reset_tokens')
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['user', 'used']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        return f"Password reset for {self.user.username} - {self.token}"
    
    def is_valid(self):
        """Check if token is valid and not expired"""
        return not self.used and timezone.now() < self.expires_at
    
    def mark_as_used(self):
        """Mark token as used"""
        self.used = True
        self.save()


class LoginAttempt(models.Model):
    """Model for tracking login attempts for security"""
    username = models.CharField(max_length=150)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    success = models.BooleanField(default=False)
    attempted_at = models.DateTimeField(auto_now_add=True)
    failure_reason = models.CharField(max_length=100, blank=True)
    
    class Meta:
        ordering = ['-attempted_at']
        indexes = [
            models.Index(fields=['username', 'attempted_at']),
            models.Index(fields=['ip_address', 'attempted_at']),
        ]
    
    def __str__(self):
        status = "Success" if self.success else "Failed"
        return f"{status} login attempt for {self.username} from {self.ip_address}"


class SecurityEvent(models.Model):
    """Model for tracking security events"""
    EVENT_TYPES = [
        ('password_reset_requested', 'Password Reset Requested'),
        ('password_reset_completed', 'Password Reset Completed'),
        ('password_changed', 'Password Changed'),
        ('account_locked', 'Account Locked'),
        ('suspicious_activity', 'Suspicious Activity'),
        ('login_from_new_device', 'Login from New Device'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='security_events', null=True, blank=True)
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES)
    description = models.TextField()
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['event_type', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.event_type} - {self.user.username if self.user else 'System'} at {self.created_at}"
