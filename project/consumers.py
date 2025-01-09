import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.exceptions import DenyConnection
from app.models import GATE_STATES, TRIGGER_TYPES, TriggerLog, GateStateLog, RegisteredECV
from asgiref.sync import sync_to_async
from django.core.cache import cache
from django.contrib.auth import get_user_model

User = get_user_model()

gate_states = list(map(lambda x: x[0], GATE_STATES))
trigger_types = list(map(lambda x: x[0], TRIGGER_TYPES))

class GateConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_name = "consumer"
        print(self.scope["user"].username)

        if self.scope["user"].is_anonymous:
            raise DenyConnection("Unauthorized")
        
        self.group_name = "gate_controller" if self.scope["user"].username == "gate_controller" else "gate_client"

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()
        await self.send(text_data=json.dumps({'type': 'success', 'message': f'Connected to {self.group_name} as {self.scope["user"].username}'}))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
    
    async def receive(self, text_data: str):
        if not text_data:
            await self.send(text_data=json.dumps({'type': 'error', 'message': 'Invalid data'}))
            return

        json_data: dict = json.loads(text_data)
        message_type = json_data.get('type', '')
        message = json_data.get('message', '')

        print("Received json: ", json.dumps(json_data) , "from", self.scope['user'].username, "at", self.group_name) 

        match message_type:
            case "status":
                if self.scope['user'].username != "gate_controller":
                    await self.send(text_data=json.dumps({'type': 'error', 'message': 'Unauthorized'}))
                    return
                
                if not message in gate_states:
                    await self.send(text_data=json.dumps({'type': 'error', 'message': 'Invalid data'}))
                    return
                
                print("Triggered by controller")

                cache.set("gate_state", message)

                possible_trigger = await sync_to_async(TriggerLog.get_trigger)()
                await sync_to_async(GateStateLog.objects.create)(
                    gate_state=message,
                    trigger=possible_trigger
                )

                await self.channel_layer.group_send(
                    "gate_client",
                    {
                        'type': 'send_status',
                        'message': message
                    }
                )

            case "trigger": 
                if not message in trigger_types:   
                    await self.send(text_data=json.dumps({'type': 'error', 'message': 'Invalid data'}))
                    return
                
                if not self.scope['user'].has_permission(message):
                    await self.send(text_data=json.dumps({'type': 'error', 'message': 'Unauthorized'}))
                    return
                
                await sync_to_async(TriggerLog.objects.create)(
                    trigger_type=message,
                    user=self.scope["user"],
                    trigger_agent="api"
                ) 
                
                print("Triggered by client")
                await self.channel_layer.group_send(
                    "gate_controller",
                    {
                        'type': 'send_trigger',
                        'message': message
                    }
                )

                await self.send(text_data=json.dumps({'type': 'success', 'message': 'Triggered'}))

            case "ecv_detected":
                if self.scope["user"].username != "rpi_controller":
                    await self.send(text_data=json.dumps({'type': 'error', 'message': 'Unauthorized'}))
                    return
                
                registered_ecv = await sync_to_async(lambda: RegisteredECV.objects.filter(ecv=message).first())()
                
                if not registered_ecv:
                    await self.send(text_data=json.dumps({'type': 'error', 'message': 'Ecv not registered'}))
                    return

                if not await sync_to_async(lambda x: registered_ecv.user.has_permission(x))("start_v") or not await sync_to_async(lambda: registered_ecv.is_allowed)():
                    await self.send(text_data=json.dumps({'type': 'error', 'message': 'Unauthorized'}))
                    return
                
                await sync_to_async(TriggerLog.objects.create)(
                    trigger_type="start_v",
                    user=registered_ecv.user,
                    ecv=registered_ecv,
                    trigger_agent="rpi"
                ) 
                
                print("Triggered by rpi")
                await self.channel_layer.group_send(
                    "gate_controller",
                    {
                        'type': 'send_trigger',
                        'message': "start_v"
                    }
                )

                await self.send(text_data=json.dumps({'type': 'success', 'message': 'Triggered'}))
            
            case _:
                await self.send(text_data=json.dumps({'type': 'error', 'message': 'Invalid data'}))


    async def send_status(self, event):
        message = event['message']
        print("Sending status update: ", message)
        await self.send(text_data=json.dumps({'type': 'status', 'message': message}))

    async def send_trigger(self, event):
        message = event['message']
        print("Sending trigger: ", message)
        await self.send(text_data=json.dumps({'type': 'trigger', 'message': message}))
        