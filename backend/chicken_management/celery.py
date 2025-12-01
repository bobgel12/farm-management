from celery import Celery
from celery.schedules import crontab
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chicken_management.settings')

app = Celery('chicken_management')
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks
app.autodiscover_tasks()

# Celery Beat schedule
app.conf.beat_schedule = {
    'scrape-rotem-data-every-5-minutes': {
        'task': 'rotem_scraper.tasks.scrape_rotem_data',
        'schedule': 300.0,  # Every 5 minutes (300 seconds)
    },
    'collect-monitoring-data-every-5-minutes': {
        'task': 'rotem_scraper.tasks.collect_monitoring_data',
        'schedule': 300.0,  # Every 5 minutes (300 seconds) - configurable
    },
    'analyze-data-every-hour': {
        'task': 'rotem_scraper.tasks.analyze_data',
        'schedule': 3600.0,  # Every hour (3600 seconds)
    },
    # Scheduled report execution (check every hour)
    'execute-due-scheduled-reports': {
        'task': 'reporting.tasks.execute_due_scheduled_reports',
        'schedule': 3600.0,  # Every hour (3600 seconds)
    },
    # Daily KPI calculations (run at midnight)
    'calculate-organization-kpis-daily': {
        'task': 'reporting.tasks.calculate_organization_kpis',
        'schedule': crontab(hour=0, minute=0),  # Daily at midnight
    },
    # Water consumption monitoring (run daily at 6 AM)
    'monitor-water-consumption-daily': {
        'task': 'houses.tasks.monitor_water_consumption',
        'schedule': crontab(hour=6, minute=0),  # Daily at 6 AM
    },
    # Cleanup old water alerts (run weekly on Sunday at 2 AM)
    'cleanup-old-water-alerts-weekly': {
        'task': 'houses.tasks.cleanup_old_water_alerts',
        'schedule': crontab(day_of_week=0, hour=2, minute=0),  # Weekly on Sunday at 2 AM
    },
}

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
