# consumer.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer

class MyConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.ws_path = self.scope['path']
        self.group_name = 'gate_status'

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()
        await self.send(text_data=json.dumps({'message': f'Connected to {self.group_name}'}))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        if self.ws_path == '/ws/secret/gate/status/':
            await self.channel_layer.group_send(
                self.group_name,
                {
                    'type': 'send_gate_status',
                    'message': text_data
                }
            )

    async def send_gate_status(self, event):
        message = event['message']
        await self.send(text_data=json.dumps({'message': message}))