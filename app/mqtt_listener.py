import os
import django
import asyncio
import websockets
import paho.mqtt.client as mqtt
from .models import GateStateHistory, TriggerHistory, GATE_STATES

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

mqtt_username = os.getenv("MQTT_USERNAME")
mqtt_password = os.getenv("MQTT_PASSWORD")
broker_address = os.getenv("MQTT_BROKER_ADDRESS")
broker_port = int(os.getenv("MQTT_BROKER_PORT"))
gate_states = list(map(lambda x: x[0], GATE_STATES))

websocket_uri = "ws://127.0.0.1:8000/ws/secret/gate/status/"

async def send_websocket_message(message):
    async with websockets.connect(websocket_uri) as websocket:
        await websocket.send(message)
        print(f"Sent message to WebSocket: {message}")

def on_message(client, userdata, msg):
    topic: str = msg.topic
    message: str = msg.payload.decode('utf-8')
    
    print(f"Received message '{message}' on topic '{topic}'")
    
    if message in gate_states:
        print(f"Gate status: {message}")
        
        possible_trigger = TriggerHistory.get_trigger()

        GateStateHistory.objects.create(gate_state=message, trigger=possible_trigger)

        asyncio.run(send_websocket_message(message))


def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))

    client.subscribe(f"gate/status")

def start_mqtt_listener():
    client = mqtt.Client()
    client.username_pw_set(mqtt_username, mqtt_password)

    client.on_connect = on_connect
    client.on_message = on_message
    
    client.connect(broker_address, broker_port, 60)
    
    client.loop_forever()

if __name__ == "__main__":
    start_mqtt_listener()
