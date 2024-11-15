import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.exceptions import DenyConnection
from app.models import GATE_STATES, TRIGGER_TYPES, TriggerHistory, GateStateHistory
from asgiref.sync import sync_to_async

gate_states = list(map(lambda x: x[0], GATE_STATES))
trigger_types = list(map(lambda x: x[0], TRIGGER_TYPES))

class GateConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_name = "gate_controller" if self.scope["user"].username == "gate_controller" else "gate_client"
        if self.scope["user"].is_anonymous:
            raise DenyConnection("Unauthorized")
        
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()
        await self.send(text_data=json.dumps({'message': f'Connected to {self.group_name} as {self.scope["user"].username}'}))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        print("Received message: ", text_data, "from", self.scope['user'].username, "at", self.group_name) 
        if self.scope['user'].username == "gate_controller":
            if text_data and text_data in gate_states:
                possible_trigger = await sync_to_async(TriggerHistory.get_trigger)()

                await sync_to_async(GateStateHistory.objects.create)(
                    gate_state=text_data,
                    trigger=possible_trigger
                )
                print("Triggered by controller")
                await self.channel_layer.group_send(
                    "gate_client",
                    {
                        'type': 'send_message',
                        'message': text_data
                    }
                )
        else:
            if text_data and text_data in trigger_types:   
                await sync_to_async(TriggerHistory.objects.create)(
                    trigger_type=text_data,
                    user=self.scope["user"],
                    trigger_agent="api"
                ) 
                print("Triggered by client")
                await self.channel_layer.group_send(
                    "gate_controller",
                    {
                        'type': 'send_message',
                        'message': text_data
                    }
                )

    async def send_message(self, event):
        message = event['message']
        print("Sending message: ", message)
        await self.send(text_data=json.dumps({'message': message}))
        