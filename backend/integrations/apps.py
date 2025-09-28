from django.apps import AppConfig


class IntegrationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'integrations'
    verbose_name = 'System Integrations'
    
    def ready(self):
        # Import signal handlers if needed
        pass