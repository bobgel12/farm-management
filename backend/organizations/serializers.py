from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Organization, OrganizationUser


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model (simplified)"""
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = ['id']


class OrganizationSerializer(serializers.ModelSerializer):
    """Serializer for Organization model"""
    total_farms = serializers.ReadOnlyField()
    total_users = serializers.ReadOnlyField()
    total_houses = serializers.ReadOnlyField()
    is_trial_expired = serializers.ReadOnlyField()
    
    class Meta:
        model = Organization
        fields = [
            'id', 'name', 'slug', 'description',
            'contact_email', 'contact_phone', 'website', 'address',
            'is_active', 'is_trial', 'trial_expires_at',
            'subscription_tier', 'subscription_status',
            'max_farms', 'max_users', 'max_houses_per_farm',
            'logo', 'primary_color', 'secondary_color', 'custom_domain',
            'created_at', 'updated_at',
            'total_farms', 'total_users', 'total_houses', 'is_trial_expired'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_slug(self, value):
        """Ensure slug is URL-friendly"""
        if not value.replace('-', '').replace('_', '').isalnum():
            raise serializers.ValidationError("Slug can only contain letters, numbers, hyphens, and underscores")
        return value.lower()


class OrganizationListSerializer(serializers.ModelSerializer):
    """Simplified serializer for organization list"""
    total_farms = serializers.ReadOnlyField()
    total_users = serializers.ReadOnlyField()
    
    class Meta:
        model = Organization
        fields = [
            'id', 'name', 'slug', 'subscription_tier', 'subscription_status',
            'is_active', 'total_farms', 'total_users', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class OrganizationUserSerializer(serializers.ModelSerializer):
    """Serializer for OrganizationUser model"""
    user = UserSerializer(read_only=True)
    user_id = serializers.IntegerField(write_only=True, required=False)
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    is_owner = serializers.ReadOnlyField()
    is_admin = serializers.ReadOnlyField()
    
    class Meta:
        model = OrganizationUser
        fields = [
            'id', 'organization', 'organization_name', 'user', 'user_id',
            'role', 'is_active',
            'can_manage_farms', 'can_manage_users', 'can_view_reports', 'can_export_data',
            'joined_at', 'updated_at', 'invited_by',
            'is_owner', 'is_admin'
        ]
        read_only_fields = ['id', 'joined_at', 'updated_at']


class OrganizationMembershipSerializer(serializers.ModelSerializer):
    """Serializer for user's organization memberships"""
    organization = OrganizationListSerializer(read_only=True)
    is_owner = serializers.ReadOnlyField()
    is_admin = serializers.ReadOnlyField()
    
    class Meta:
        model = OrganizationUser
        fields = [
            'id', 'organization', 'role', 'is_active',
            'can_manage_farms', 'can_manage_users', 'can_view_reports', 'can_export_data',
            'joined_at', 'is_owner', 'is_admin'
        ]
        read_only_fields = ['id', 'joined_at']

