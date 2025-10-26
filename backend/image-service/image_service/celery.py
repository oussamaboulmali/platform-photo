"""
Celery configuration for image_service
"""
import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'image_service.settings')

app = Celery('image_service')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Periodic tasks
app.conf.beat_schedule = {
    'expire-download-tokens': {
        'task': 'images.tasks.expire_download_tokens',
        'schedule': crontab(minute='*/15'),  # Every 15 minutes
    },
}
