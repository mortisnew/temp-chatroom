import json
from urllib.parse import parse_qs

import redis
from asgiref.sync import sync_to_async
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from .models import ChatRoom, Message, NickName


class ChatConsumer(AsyncWebsocketConsumer):

    # =========================
    # LIMITS
    # =========================

    NICKNAME_MAX_LENGTH = 100
    MESSAGE_MAX_LENGTH = 2000

    PRESENCE_TTL = 30

    MESSAGE_RATE_LIMIT = 30
    MESSAGE_RATE_WINDOW = 60

    MESSAGE_COOLDOWN = 1


    # =========================
    # CONNECT
    # =========================

    async def connect(self):

        self.room_code = (
            self.scope["url_route"]["kwargs"]["room_code"]
        )

        self.room_group_name = (
            f"chat_{self.room_code}"
        )

        self.nickname = ""

        query_string = parse_qs(
            self.scope["query_string"].decode()
        )

        self.nickname = query_string.get(
            "nickname",
            [""]
        )[0].strip()


        # =========================
        # NICKNAME VALIDATION
        # =========================

        if not self.nickname:
            await self.close()
            return


        if len(self.nickname) > self.NICKNAME_MAX_LENGTH:
            await self.close()
            return


        # =========================
        # ROOM VALIDATION
        # =========================

        room_exists = await self.check_room()

        if not room_exists:
            await self.close()
            return


        # =========================
        # NICKNAME CLAIM
        # =========================

        nickname_claimed = (
            await self.claim_nickname()
        )

        if not nickname_claimed:

            await self.close(code=4001)

            return


        # =========================
        # CONNECT
        # =========================

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()


        # =========================
        # ONLINE PRESENCE
        # =========================

        await self.add_online_member()


        # =========================
        # MESSAGE HISTORY
        # =========================

        history = (
            await self.get_message_history()
        )

        for message in history:

            await self.send(
                text_data=json.dumps({
                    "type": "message",
                    "nickname": message["nickname"],
                    "message": message["message"],
                    "created_at": message["created_at"],
                })
            )


        # =========================
        # ONLINE MEMBERS
        # =========================

        online_members = (
            await self.get_online_members()
        )

        await self.send(
            text_data=json.dumps({
                "type": "online_members",
                "members": online_members,
            })
        )


        # =========================
        # JOIN EVENT
        # =========================

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "user_joined",
                "nickname": self.nickname,
                "channel_name": self.channel_name,
            }
        )


    # =========================
    # DISCONNECT
    # =========================

    async def disconnect(self, close_code):

        if not self.nickname:
            return


        await self.release_nickname()

        await self.remove_online_member()


        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "user_left",
                "nickname": self.nickname,
                "channel_name": self.channel_name,
            }
        )


        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )


    # =========================
    # RECEIVE
    # =========================

    async def receive(self, text_data):

        try:

            data = json.loads(
                text_data
            )

        except json.JSONDecodeError:

            return


        # =========================
        # HEARTBEAT
        # =========================

        if data.get("type") == "ping":

            await self.refresh_online_member()

            await self.refresh_nickname_claim()

            return


        # =========================
        # MESSAGE
        # =========================

        message = data.get(
            "message",
            ""
        )


        if not isinstance(message, str):
            return


        message = message.strip()


        if not message:
            return


        # =========================
        # MESSAGE LENGTH
        # =========================

        if len(message) > self.MESSAGE_MAX_LENGTH:

            await self.send(
                text_data=json.dumps({
                    "type": "error",
                    "message": (
                        "Message must be "
                        "2000 characters or less."
                    ),
                })
            )

            return


        # =========================
        # MESSAGE COOLDOWN
        # =========================

        cooldown_allowed = (
            await self.check_message_cooldown()
        )

        if not cooldown_allowed:

            await self.send(
                text_data=json.dumps({
                    "type": "error",
                    "message": (
                        "Please wait before "
                        "sending another message."
                    ),
                })
            )

            return


        # =========================
        # MESSAGE RATE LIMIT
        # =========================

        rate_allowed = (
            await self.check_message_rate_limit()
        )

        if not rate_allowed:

            await self.send(
                text_data=json.dumps({
                    "type": "error",
                    "message": (
                        "You have reached the "
                        "message limit. "
                        "Please try again later."
                    ),
                })
            )

            return


        # =========================
        # SAVE MESSAGE
        # =========================

        await self.save_message(
            nickname=self.nickname,
            message=message
        )


        # =========================
        # BROADCAST
        # =========================

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "nickname": self.nickname,
                "message": message,
            }
        )


    # =========================
    # CHAT MESSAGE
    # =========================

    async def chat_message(self, event):

        await self.send(
            text_data=json.dumps({
                "type": "message",
                "nickname": event["nickname"],
                "message": event["message"],
            })
        )


    # =========================
    # USER JOINED
    # =========================

    async def user_joined(self, event):

        if (
            event["channel_name"]
            == self.channel_name
        ):
            return


        await self.send(
            text_data=json.dumps({
                "type": "user_joined",
                "nickname": event["nickname"],
            })
        )


    # =========================
    # USER LEFT
    # =========================

    async def user_left(self, event):

        if (
            event["channel_name"]
            == self.channel_name
        ):
            return


        await self.send(
            text_data=json.dumps({
                "type": "user_left",
                "nickname": event["nickname"],
            })
        )


    # =========================
    # REDIS KEYS
    # =========================

    def get_presence_key(self):

        return (
            f"chatroom:"
            f"{self.room_code}:"
            f"member:"
            f"{self.channel_name}"
        )


    def get_nickname_key(self):

        normalized_nickname = (
            self.nickname.lower()
        )

        return (
            f"chatroom:"
            f"{self.room_code}:"
            f"nickname:"
            f"{normalized_nickname}"
        )


    def get_message_rate_key(self):

        normalized_nickname = (
            self.nickname.lower()
        )

        return (
            f"chatroom:"
            f"{self.room_code}:"
            f"rate:"
            f"{normalized_nickname}"
        )


    def get_message_cooldown_key(self):

        normalized_nickname = (
            self.nickname.lower()
        )

        return (
            f"chatroom:"
            f"{self.room_code}:"
            f"cooldown:"
            f"{normalized_nickname}"
        )


    # =========================
    # NICKNAME CLAIM
    # =========================

    @sync_to_async
    def claim_nickname(self):

        client = redis.Redis(
            host="127.0.0.1",
            port=6379,
            decode_responses=True,
        )

        claimed = client.set(
            self.get_nickname_key(),
            self.channel_name,
            ex=self.PRESENCE_TTL,
            nx=True,
        )

        client.close()

        return claimed is True


    @sync_to_async
    def refresh_nickname_claim(self):

        client = redis.Redis(
            host="127.0.0.1",
            port=6379,
            decode_responses=True,
        )

        key = self.get_nickname_key()

        owner = client.get(key)


        if owner == self.channel_name:

            client.expire(
                key,
                self.PRESENCE_TTL,
            )


        client.close()


    @sync_to_async
    def release_nickname(self):

        client = redis.Redis(
            host="127.0.0.1",
            port=6379,
            decode_responses=True,
        )

        key = self.get_nickname_key()

        owner = client.get(key)


        if owner == self.channel_name:

            client.delete(key)


        client.close()


    # =========================
    # MESSAGE COOLDOWN
    # =========================

    @sync_to_async
    def check_message_cooldown(self):

        client = redis.Redis(
            host="127.0.0.1",
            port=6379,
            decode_responses=True,
        )

        key = (
            self.get_message_cooldown_key()
        )


        allowed = client.set(
            key,
            "1",
            ex=self.MESSAGE_COOLDOWN,
            nx=True,
        )


        client.close()

        return allowed is True


    # =========================
    # MESSAGE RATE LIMIT
    # =========================

    @sync_to_async
    def check_message_rate_limit(self):

        client = redis.Redis(
            host="127.0.0.1",
            port=6379,
            decode_responses=True,
        )

        key = (
            self.get_message_rate_key()
        )


        count = client.incr(key)


        if count == 1:

            client.expire(
                key,
                self.MESSAGE_RATE_WINDOW
            )


        allowed = (
            count <= self.MESSAGE_RATE_LIMIT
        )


        client.close()

        return allowed


    # =========================
    # PRESENCE
    # =========================

    @sync_to_async
    def add_online_member(self):

        client = redis.Redis(
            host="127.0.0.1",
            port=6379,
            decode_responses=True,
        )

        client.set(
            self.get_presence_key(),
            self.nickname,
            ex=self.PRESENCE_TTL,
        )

        client.close()


    @sync_to_async
    def refresh_online_member(self):

        client = redis.Redis(
            host="127.0.0.1",
            port=6379,
            decode_responses=True,
        )

        client.expire(
            self.get_presence_key(),
            self.PRESENCE_TTL,
        )

        client.close()


    @sync_to_async
    def remove_online_member(self):

        client = redis.Redis(
            host="127.0.0.1",
            port=6379,
            decode_responses=True,
        )

        client.delete(
            self.get_presence_key()
        )

        client.close()


    @sync_to_async
    def get_online_members(self):

        client = redis.Redis(
            host="127.0.0.1",
            port=6379,
            decode_responses=True,
        )

        pattern = (
            f"chatroom:"
            f"{self.room_code}:"
            f"member:*"
        )

        members = []


        for key in client.scan_iter(
            match=pattern
        ):

            nickname = client.get(key)


            if nickname is None:
                continue


            member_id = (
                key.rsplit(":", 1)[-1]
            )


            members.append({
                "id": member_id,
                "nickname": nickname,
            })


        client.close()

        return members


    # =========================
    # DATABASE
    # =========================

    @database_sync_to_async
    def check_room(self):

        return ChatRoom.objects.filter(
            room_code=self.room_code,
            active=True,
        ).exists()


    @database_sync_to_async
    def save_message(
        self,
        nickname,
        message
    ):

        chat = ChatRoom.objects.get(
            room_code=self.room_code
        )


        nickname_obj, created = (
            NickName.objects.get_or_create(
                chat=chat,
                nickname=nickname,
            )
        )


        Message.objects.create(
            chat=chat,
            nickname=nickname_obj,
            message=message,
        )


    @database_sync_to_async
    def get_message_history(self):

        chat = ChatRoom.objects.get(
            room_code=self.room_code
        )


        messages = (
            Message.objects
            .filter(chat=chat)
            .select_related("nickname")
            .order_by("created_at")[:100]
        )


        return [
            {
                "nickname":
                    message.nickname.nickname,

                "message":
                    message.message,

                "created_at":
                    message.created_at.isoformat(),
            }

            for message in messages
        ]

