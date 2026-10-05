from celery import Celery
from datetime import timedelta
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
celery_app = Celery('config')
celery_app.autodiscover_tasks()
celery_app.conf.update(
        broker_url = 'redis://127.0.0.1:6379/0',
        result_backend = 'redis://127.0.0.1:6379/1',
        task_serializer = 'json',
        result_serializer = 'json',
        result_expires = timedelta(days=7),
        task_always_eager = False,
        worker_prefetch_multiplier = 4,
        beat_scheduler = 'django_celery_beat.schedulers:DatabaseScheduler',
)
