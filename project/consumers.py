import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.exceptions import DenyConnection
from app.models import GATE_STATES, TRIGGER_TYPES, TriggerHistory, GateStateHistory

gate_states = map(lambda x: x[0], GATE_STATES)
trigger_types = map(lambda x: x[0], TRIGGER_TYPES)

class GateStatusConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_name = 'gate_status'
        
        if self.scope["user"].is_anonymous:
            raise DenyConnection("Unauthorized")

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
        if self.scope["user"] != "gate_controller":
            raise DenyConnection("Unauthorized")
        
        if text_data in gate_states:
            possible_trigger = TriggerHistory.get_trigger()

            GateStateHistory.objects.create(gate_state=text_data, trigger=possible_trigger)
        
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


class GateTriggerConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_name = "gate_controller" if self.scope["user"].username == "gate_controller" else "gate_trigger"
        
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
        if text_data in trigger_types:            
            TriggerHistory.objects.create(trigger=text_data, user=self.scope["user"], trigger_agent="api")
        
            await self.channel_layer.group_send(
                "gate_controller",
                {
                    'type': 'send_trigger',
                    'message': text_data
                }
            )

    async def send_trigger(self, event):
        message = event['message']
        await self.send(text_data=json.dumps({'message': message}))