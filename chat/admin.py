from django.contrib import admin
from chat.models import ChatRoom,Message,NickName

admin.site.register(ChatRoom)
admin.site.register(Message)
admin.site.register(NickName)

