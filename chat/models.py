from datetime import timedelta
from django.db import models
from django.utils import timezone

class ChatRoom(models.Model):
    title = models.CharField(max_length=100)
    room_code = models.CharField(
        max_length=12,
        unique=True,
        editable=False
    )
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expired_at = models.DateTimeField(blank=True, null=True)
    active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if self.expired_at is None:
            self.expired_at = timezone.now() + timedelta(minutes=30)
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.title} | {self.created_at} | {self.expired_at}'

class NickName(models.Model):
    chat = models.ForeignKey(ChatRoom, on_delete=models.CASCADE,related_name='nicknames')
    nickname = models.CharField(max_length=100)

class Message(models.Model):
    chat = models.ForeignKey(ChatRoom, on_delete=models.CASCADE,related_name='messages')
    nickname = models.ForeignKey(NickName, on_delete=models.CASCADE,related_name='messages')
    message = models.TextField(max_length=2000)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f'{self.chat} | {self.message}'