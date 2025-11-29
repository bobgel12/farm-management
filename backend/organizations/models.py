"""
Organization/Company models for multi-tenancy support
"""
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import EmailValidator, URLValidator
import uuid


class Organization(models.Model):
    """Organization/Company model for multi-tenancy"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, unique=True, help_text="Organization name")
    slug = models.SlugField(max_length=200, unique=True, help_text="URL-friendly identifier")
    description = models.TextField(blank=True, help_text="Organization description")
    
    # Contact Information
    contact_email = models.EmailField(validators=[EmailValidator()])
    contact_phone = models.CharField(max_length=20, blank=True)
    website = models.URLField(blank=True, validators=[URLValidator()])
    address = models.TextField(blank=True)
    
    # Organization Settings
    is_active = models.BooleanField(default=True, help_text="Whether the organization is active")
    is_trial = models.BooleanField(default=False, help_text="Whether organization is on trial")
    trial_expires_at = models.DateTimeField(null=True, blank=True, help_text="Trial expiration date")
    
    # Subscription & Billing
    subscription_tier = models.CharField(
        max_length=50,
        choices=[
            ('trial', 'Trial'),
            ('basic', 'Basic'),
            ('standard', 'Standard'),
            ('premium', 'Premium'),
            ('enterprise', 'Enterprise'),
        ],
        default='trial',
        help_text="Subscription tier"
    )
    subscription_status = models.CharField(
        max_length=20,
        choices=[
            ('active', 'Active'),
            ('suspended', 'Suspended'),
            ('cancelled', 'Cancelled'),
            ('expired', 'Expired'),
        ],
        default='active',
        help_text="Subscription status"
    )
    
    # Usage Limits
    max_farms = models.IntegerField(default=10, help_text="Maximum number of farms")
    max_users = models.IntegerField(default=5, help_text="Maximum number of users")
    max_houses_per_farm = models.IntegerField(default=20, help_text="Maximum houses per farm")
    
    # White-labeling
    logo = models.ImageField(upload_to='organizations/logos/', null=True, blank=True)
    primary_color = models.CharField(max_length=7, default='#1976d2', help_text="Primary brand color (hex)")
    secondary_color = models.CharField(max_length=7, default='#dc004e', help_text="Secondary brand color (hex)")
    custom_domain = models.CharField(max_length=255, blank=True, help_text="Custom domain for white-labeling")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_organizations'
    )
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Organization'
        verbose_name_plural = 'Organizations'
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['is_active']),
            models.Index(fields=['subscription_status']),
        ]
    
    def __str__(self):
        return self.name
    
    @property
    def total_farms(self):
        """Get total number of farms in this organization"""
        return self.farms.count()
    
    @property
    def total_users(self):
        """Get total number of users in this organization"""
        return self.organization_users.count()
    
    @property
    def total_houses(self):
        """Get total number of houses across all farms"""
        from farms.models import Farm
        total = 0
        for farm in self.farms.all():
            total += farm.total_houses
        return total
    
    @property
    def is_trial_expired(self):
        """Check if trial has expired"""
        if not self.is_trial or not self.trial_expires_at:
            return False
        return timezone.now() > self.trial_expires_at
    
    def can_add_farm(self):
        """Check if organization can add more farms"""
        return self.total_farms < self.max_farms
    
    def can_add_user(self):
        """Check if organization can add more users"""
        return self.total_users < self.max_users


class OrganizationUser(models.Model):
    """Relationship between users and organizations with roles"""
    ROLE_CHOICES = [
        ('owner', 'Owner'),
        ('admin', 'Administrator'),
        ('manager', 'Manager'),
        ('worker', 'Worker'),
        ('viewer', 'Viewer'),
    ]
    
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='organization_users'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='organization_memberships'
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='worker')
    is_active = models.BooleanField(default=True)
    
    # Additional permissions
    can_manage_farms = models.BooleanField(default=False, help_text="Can create/edit/delete farms")
    can_manage_users = models.BooleanField(default=False, help_text="Can manage organization users")
    can_view_reports = models.BooleanField(default=True, help_text="Can view reports")
    can_export_data = models.BooleanField(default=False, help_text="Can export data")
    
    # Metadata
    joined_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    invited_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invited_users'
    )
    
    class Meta:
        unique_together = ['organization', 'user']
        ordering = ['organization', 'user']
        verbose_name = 'Organization User'
        verbose_name_plural = 'Organization Users'
        indexes = [
            models.Index(fields=['organization', 'is_active']),
            models.Index(fields=['user', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.organization.name} ({self.role})"
    
    @property
    def is_owner(self):
        """Check if user is organization owner"""
        return self.role == 'owner'
    
    @property
    def is_admin(self):
        """Check if user is admin or owner"""
        return self.role in ['owner', 'admin']
    
    def has_permission(self, permission):
        """Check if user has specific permission"""
        if self.is_owner or self.is_admin:
            return True
        
        permission_map = {
            'manage_farms': self.can_manage_farms,
            'manage_users': self.can_manage_users,
            'view_reports': self.can_view_reports,
            'export_data': self.can_export_data,
        }
        
        return permission_map.get(permission, False)


class OrganizationInvite(models.Model):
    """Invitation to join an organization"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='invites'
    )
    email = models.EmailField(validators=[EmailValidator()], help_text="Email address to invite")
    token = models.CharField(max_length=64, unique=True, help_text="Unique invite token")
    
    # Invite details
    role = models.CharField(max_length=20, choices=OrganizationUser.ROLE_CHOICES, default='worker')
    can_manage_farms = models.BooleanField(default=False)
    can_manage_users = models.BooleanField(default=False)
    can_view_reports = models.BooleanField(default=True)
    can_export_data = models.BooleanField(default=False)
    
    # Status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    expires_at = models.DateTimeField(help_text="When the invite expires")
    
    # Metadata
    invited_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='sent_invites'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    accepted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='accepted_invites'
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Organization Invite'
        verbose_name_plural = 'Organization Invites'
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['email']),
            models.Index(fields=['organization', 'status']),
        ]
    
    def __str__(self):
        return f"Invite to {self.organization.name} for {self.email}"
    
    @property
    def is_expired(self):
        """Check if invite has expired"""
        return timezone.now() > self.expires_at
    
    @property
    def is_valid(self):
        """Check if invite is valid (pending and not expired)"""
        return self.status == 'pending' and not self.is_expired
    
    def mark_expired(self):
        """Mark invite as expired"""
        self.status = 'expired'
        self.save(update_fields=['status', 'updated_at'])
    
    def mark_accepted(self, user):
        """Mark invite as accepted"""
        self.status = 'accepted'
        self.accepted_at = timezone.now()
        self.accepted_by = user
        self.save(update_fields=['status', 'accepted_at', 'accepted_by', 'updated_at'])
    
    def cancel(self):
        """Cancel the invite"""
        self.status = 'cancelled'
        self.save(update_fields=['status', 'updated_at'])

