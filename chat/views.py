from typing import Any
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from .models import ChatRoom,NickName,Message
from chat.serializers import (NickNameSerializer,ChatSerializerList,
                              ChatRoomSerializer,MessageSerializer)
from utils import generate_room_code
from django.shortcuts import render

from django.views.decorators.csrf import ensure_csrf_cookie


@ensure_csrf_cookie
def home(request):
    return render(request, 'chat/home.html')

def room(request,room_code):
    return render(request, 'chat/room.html',
                  {'room_code':room_code})

class ChatViewSet(viewsets.ModelViewSet):
    queryset = ChatRoom.objects.all()
    serializer_class = ChatRoomSerializer
    http_method_names = ['post']

    def get_serializer_class(self):
        if self.action == 'list':
            return ChatSerializerList
        return ChatRoomSerializer

    def create(self, request: Request, *args: Any, **kwargs: Any):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(room_code=generate_room_code())
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class MessageViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Message.objects.all()
    serializer_class = MessageSerializer

class NickNameViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = NickName.objects.all()
    serializer_class = NickNameSerializer