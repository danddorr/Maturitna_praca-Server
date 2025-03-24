import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.exceptions import DenyConnection
from app.models import *
from asgiref.sync import sync_to_async
from django.core.cache import cache
from django.contrib.auth import get_user_model
from urllib.parse import parse_qs

User = get_user_model()

class GateConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        query_string = parse_qs(self.scope["query_string"].decode())
        temp_access_link = query_string.get("temp_access_link", None)

        if temp_access_link:
            temp_access = await sync_to_async(lambda: TemporaryAccess.objects.filter(link=temp_access_link[0]).first())()
            if temp_access:
                self.scope["temp_access"] = temp_access
            else:
                raise DenyConnection("Unauthorized")
                
        if self.scope["user"].username == "gate_controller":
            self.group_name = "gate_controller"
            self.scope["agent"] = "manual"
        elif self.scope["user"].username == "rpi_controller":
            self.group_name = "rpi_controller"
            self.scope["agent"] = "rpi"
        elif not self.scope["user"].is_anonymous:
            self.group_name = "gate_client"
            self.scope["agent"] = "user"
        elif temp_access:
            self.group_name = "gate_client"
            self.scope["agent"] = "temp"
            self.scope["user"] = await sync_to_async(lambda: temp_access.user)()
        else:
            self.group_name = "Unauthorized"
            raise DenyConnection("Unauthorized")

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
 
        await self.accept()
        await self.send(text_data=json.dumps({'type': 'success', 'message': f'Connected to {self.group_name} as {self.scope["user"].username if self.scope["agent"] == "user" else "temp_access"}'}))

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
                
                if not message in GATE_STATES:
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
                if not message in TRIGGER_TYPES:   
                    await self.send(text_data=json.dumps({'type': 'error', 'message': 'Invalid data'}))
                    return
                
                if not self.scope['user'].has_permission(message):
                    await self.send(text_data=json.dumps({'type': 'error', 'message': 'Unauthorized'}))
                    return
                
                temp_access = self.scope.get("temp_access", None)

                if temp_access:
                    errors = await sync_to_async(lambda: temp_access.validate(message))()
                    if errors:
                        await self.send(text_data=json.dumps({'type': 'error', 'message': errors}))
                        return
                
                    await sync_to_async(temp_access.decrement)(message)
                
                await sync_to_async(TriggerLog.objects.create)(
                    trigger_type=message,
                    user=self.scope["user"],
                    temporary_access=temp_access,
                    trigger_agent=self.scope["agent"]
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
                
                camera_position = json_data.get('camera_position', '')

                if not camera_position or not camera_position in CAMERA_POSITIONS:
                    await self.send(text_data=json.dumps({'type': 'error', 'message': 'Invalid data'}))
                    return

                ecv_object = await sync_to_async(lambda: RegisteredECV.objects.filter(ecv=message).first())()
                ecv_type = "registered_ecv" if ecv_object else "temp_ecv"
                
                if ecv_type == "temp_ecv":
                    ecv_object = await sync_to_async(lambda: TemporaryAccess.objects.filter(ecv=message).first())()
                    if not ecv_object:
                        await self.send(text_data=json.dumps({'type': 'error', 'message': 'Ecv not registered'}))
                        return

                if camera_position == "outside":
                    if (ecv_type == "registered_ecv" and not await sync_to_async(lambda: ecv_object.is_allowed)()) or (ecv_type == "temp_ecv" and ecv_object.validate("start_v") ): 
                        await self.send(text_data=json.dumps({'type': 'error', 'message': 'Unauthorized'}))
                        return 
                    
                    if ecv_type == "temp_ecv":
                        await sync_to_async(ecv_object.decrement)("start_v")
                    
                    await sync_to_async(ParkedVehicle.objects.create)(
                        ecv=ecv_object.ecv
                    )
                    
                elif camera_position == "inside":
                    parked_vehicle = await sync_to_async(lambda: ParkedVehicle.objects.filter(ecv=ecv_object.ecv).order_by("entered_at").last())()

                    if parked_vehicle and not await sync_to_async(lambda: parked_vehicle.exited_at)():
                        
                        parked_vehicle.exited_at = timezone.now()
                        await sync_to_async(parked_vehicle.save)()
                    else:
                        await sync_to_async(ParkedVehicle.objects.create)(
                            ecv=ecv_object.ecv,
                            exited_at=timezone.now()
                        )
                        await self.send(text_data=json.dumps({'type': 'error', 'message': 'Vehicle is not parked. Opening anyway'}))
                
                await sync_to_async(TriggerLog.objects.create)(
                    trigger_type="start_v",
                    user=await sync_to_async(lambda: ecv_object.user)(),
                    ecv=ecv_object if ecv_type == "registered_ecv" else None,
                    trigger_agent="rpi",
                    camera_position=camera_position,
                    temporary_access=ecv_object if ecv_type == "temp_ecv" else None
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
        