from django.utils import timezone
from datetime import timedelta
from celery import shared_task

from chat.models import ChatRoom

@shared_task
def deactivate_expired_rooms():
    ChatRoom.objects.filter(active=True,
                            expired_at__lte=timezone.now()
                            ).update(active=False)

@shared_task
def delete_expired_rooms():
    ChatRoom.objects.filter(
        active=False,
        expired_at__lte=timezone.now() - timedelta(minutes=5)
    ).delete()
