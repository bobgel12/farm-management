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
}

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
