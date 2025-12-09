import json
from channels.generic.websocket import AsyncWebsocketConsumer

class ReplyConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        
        if not self.user.is_authenticated:
            await self.close()
            return

        self.room_group_name = f'user_{self.user.id}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def send_reply(self, event):
        message = event['message']
        
        await self.send(text_data=json.dumps({
            'message': message
        }))