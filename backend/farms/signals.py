"""
Django signals for farms app
"""
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.core.management import call_command
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


@receiver(post_migrate)
def create_default_program(sender, **kwargs):
    """
    Create default program after migrations are complete
    This ensures the default program exists in both development and production
    """
    # Only run this for the farms app
    if sender.name == 'farms':
        try:
            # Check if we're in a test environment
            if hasattr(settings, 'TESTING') and settings.TESTING:
                return
                
            # Check if we're running migrations
            if kwargs.get('using') != 'default':
                return
                
            logger.info("Ensuring default program exists after migration...")
            call_command('ensure_default_program', verbosity=0)
            logger.info("Default program check completed")
            
        except Exception as e:
            logger.error(f"Failed to create default program after migration: {str(e)}")
            # Don't raise the exception to avoid breaking migrations
