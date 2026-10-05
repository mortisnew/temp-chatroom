from rest_framework import serializers
from chat.models import Message,ChatRoom,NickName
from datetime import datetime,timedelta,timezone

class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ('id','chat','message','nickname')

class ChatRoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatRoom
        fields = ('id','title','room_code',
                  'description','created_at','expired_at','active')
        read_only_fields = ('created_at','expired_at','room_code','active')


class NickNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = NickName
        fields = ('id','chat','nickname')

class ChatSerializerList(serializers.ModelSerializer):
    class Meta:
        model = ChatRoom
        fields = ('id','active','created_at','expired_at')
        read_only_fields = ('created_at','expired_at','active','id')