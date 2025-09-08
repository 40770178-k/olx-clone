import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import Conversation, Message

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope["user"]
        if not user.is_authenticated:
            await self.close()
            return

        self.conversation_id = self.scope["url_route"]["kwargs"]["conversation_id"]
        self.group_name = f"conversation_{self.conversation_id}"
        # verify user belongs to this conversation
        allowed = await database_sync_to_async(self._user_in_conversation)()
        if not allowed:
            await self.close()
            return

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    def _user_in_conversation(self):
        try:
            conv = Conversation.objects.get(pk=self.conversation_id)
        except Conversation.DoesNotExist:
            return False
        user = self.scope["user"]
        return conv.buyer_id == user.id or conv.seller_id == user.id

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data.get("message")
        if not message:
            return

        user = self.scope["user"]
        # persist message
        msg_obj = await database_sync_to_async(self._create_message)(user.id, message)
        payload = {
            "id": msg_obj.id,
            "sender_id": user.id,
            "sender_username": str(user),
            "message": msg_obj.content,
            "created_at": msg_obj.created_at.isoformat(),
            "conversation_id": self.conversation_id,
        }
        # broadcast to group
        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "chat.message",
                "payload": payload,
            }
        )

    def _create_message(self, sender_id, message_text):
        conv = Conversation.objects.get(pk=self.conversation_id)
        user = User.objects.get(pk=sender_id)
        msg = Message.objects.create(conversation=conv, sender=user, content=message_text)
        conv.touch()
        return msg

    async def chat_message(self, event):
        payload = event["payload"]
        await self.send(text_data=json.dumps(payload))
