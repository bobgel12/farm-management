from django.contrib import admin
from .models import Organization, OrganizationUser, OrganizationInvite


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'subscription_tier', 'subscription_status', 'is_active', 'total_farms', 'total_users', 'created_at']
    list_filter = ['subscription_tier', 'subscription_status', 'is_active', 'is_trial']
    search_fields = ['name', 'slug', 'contact_email']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'name', 'slug', 'description')
        }),
        ('Contact Information', {
            'fields': ('contact_email', 'contact_phone', 'website', 'address')
        }),
        ('Subscription', {
            'fields': ('subscription_tier', 'subscription_status', 'is_trial', 'trial_expires_at')
        }),
        ('Usage Limits', {
            'fields': ('max_farms', 'max_users', 'max_houses_per_farm')
        }),
        ('White-labeling', {
            'fields': ('logo', 'primary_color', 'secondary_color', 'custom_domain')
        }),
        ('Status', {
            'fields': ('is_active', 'created_by')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(OrganizationUser)
class OrganizationUserAdmin(admin.ModelAdmin):
    list_display = ['user', 'organization', 'role', 'is_active', 'can_manage_farms', 'can_manage_users', 'joined_at']
    list_filter = ['role', 'is_active', 'organization']
    search_fields = ['user__username', 'user__email', 'organization__name']
    readonly_fields = ['joined_at', 'updated_at']
    
    fieldsets = (
        ('Membership', {
            'fields': ('organization', 'user', 'role', 'is_active')
        }),
        ('Permissions', {
            'fields': ('can_manage_farms', 'can_manage_users', 'can_view_reports', 'can_export_data')
        }),
        ('Metadata', {
            'fields': ('invited_by', 'joined_at', 'updated_at')
        }),
    )


@admin.register(OrganizationInvite)
class OrganizationInviteAdmin(admin.ModelAdmin):
    list_display = ['email', 'organization', 'role', 'status', 'expires_at', 'invited_by', 'created_at']
    list_filter = ['status', 'role', 'organization']
    search_fields = ['email', 'organization__name', 'invited_by__username']
    readonly_fields = ['id', 'token', 'created_at', 'updated_at', 'accepted_at', 'accepted_by']
    
    fieldsets = (
        ('Invite Details', {
            'fields': ('id', 'organization', 'email', 'token', 'status')
        }),
        ('Role & Permissions', {
            'fields': ('role', 'can_manage_farms', 'can_manage_users', 'can_view_reports', 'can_export_data')
        }),
        ('Timing', {
            'fields': ('expires_at', 'created_at', 'updated_at')
        }),
        ('Tracking', {
            'fields': ('invited_by', 'accepted_at', 'accepted_by')
        }),
    )
