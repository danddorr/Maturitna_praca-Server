import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.exceptions import DenyConnection
from app.models import *
from asgiref.sync import sync_to_async
from django.core.cache import cache
from django.contrib.auth import get_user_model

User = get_user_model()

gate_states = list(map(lambda x: x[0], GATE_STATES))
trigger_types = list(map(lambda x: x[0], TRIGGER_TYPES))
camera_positions = list(map(lambda x: x[0], CAMERA_POSITIONS))

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

        if not message_type or not message:
            await self.send(text_data=json.dumps({'type': 'error', 'message': 'Invalid data'}))

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
                camera_position = json_data.get('camera_position', '')

                if not camera_position or not camera_position in camera_positions:
                    await self.send(text_data=json.dumps({'type': 'error', 'message': 'Invalid data'}))
                    return
                
                if self.scope["user"].username != "rpi_controller":
                    await self.send(text_data=json.dumps({'type': 'error', 'message': 'Unauthorized'}))
                    return
                
                registered_ecv = await sync_to_async(lambda: RegisteredECV.objects.filter(ecv=message).first())()
                
                if not registered_ecv:
                    await self.send(text_data=json.dumps({'type': 'error', 'message': 'Ecv not registered'}))
                    return
                
                if camera_position == "outside":
                    if not await sync_to_async(lambda x: registered_ecv.user.has_permission(x))("start_v") or not await sync_to_async(lambda: registered_ecv.is_allowed)():
                        await self.send(text_data=json.dumps({'type': 'error', 'message': 'Unauthorized'}))
                        return
                    
                    parked_vehicle = await sync_to_async(lambda: ParkedVehicle.objects.filter(ecv=registered_ecv).order_by("entered_at").last())()

                    if parked_vehicle:
                        time_inside = timezone.now() - parked_vehicle.entered_at
                        if time_inside.total_seconds() < 15:
                            await self.send(text_data=json.dumps({'type': 'error', 'message': 'Vehicle has not been inside long enough'}))
                            return
                    
                    #ak bolo zaparkovane vozidlo poslednych 15 sekund a naskenovala ho vonkajsia kamera tak ignoruj
                    was_parked = await sync_to_async(ParkedVehicle.objects.filter(ecv=registered_ecv, exited_at__gte=timezone.now() - timedelta(seconds=15)).exists)()
                    if was_parked:
                        await self.send(text_data=json.dumps({'type': 'error', 'message': 'Vehicle is just leaving'}))
                        return
                    
                    await sync_to_async(ParkedVehicle.objects.create)(
                        ecv=registered_ecv
                    )
                    #################nefuguje dako vzdy to zapise 3x ked to vidi
                elif camera_position == "inside":
                    #zobrat len uplne najnovsi zaznam o zaparkovani tohto vozidla zoradene podla entered_at
                    parked_vehicle = await sync_to_async(lambda: ParkedVehicle.objects.filter(ecv=registered_ecv).order_by("entered_at").last())()

                    if parked_vehicle:
                        time_inside = timezone.now() - parked_vehicle.entered_at
                        if time_inside.total_seconds() < 15:
                            await self.send(text_data=json.dumps({'type': 'error', 'message': 'Vehicle has not been inside long enough'}))
                            return
                    
                    print(await sync_to_async(lambda: parked_vehicle.ecv)())
                    print(await sync_to_async(lambda: parked_vehicle.exited_at)())
                    #ak je zaparkovane vozidlo a naskenovala ho vnutorna kamera
                    if parked_vehicle and not await sync_to_async(lambda: parked_vehicle.exited_at)():
                        #ak je vozidlo v parkovisku viac ako 15 sekund ukonci parkovanie
                        
                        parked_vehicle.exited_at = timezone.now()
                        await sync_to_async(parked_vehicle.save)()
                    else:
                        await sync_to_async(ParkedVehicle.objects.create)(
                            ecv=registered_ecv,
                            exited_at=timezone.now()
                        )
                        await self.send(text_data=json.dumps({'type': 'error', 'message': 'Vehicle is not parked. Opening anyway'}))
                    #ak nie je zaparkovane vozidlo a naskenovala ho vnutorna kamera tak otvor branu
                
                await sync_to_async(TriggerLog.objects.create)(
                    trigger_type="start_v",
                    user=await sync_to_async(lambda: registered_ecv.user)(),
                    ecv=registered_ecv,
                    trigger_agent="rpi",
                    camera_position=camera_position
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
        