"""
Signals for organizations app
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Organization, OrganizationUser


@receiver(post_save, sender=Organization)
def create_default_owner(sender, instance, created, **kwargs):
    """Create default owner when organization is created"""
    if created and instance.created_by:
        OrganizationUser.objects.create(
            organization=instance,
            user=instance.created_by,
            role='owner',
            can_manage_farms=True,
            can_manage_users=True,
            can_view_reports=True,
            can_export_data=True,
            invited_by=instance.created_by
        )

