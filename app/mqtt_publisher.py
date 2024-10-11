import os
from dotenv import load_dotenv
import paho.mqtt.client as mqtt
from .models import TRIGGER_TYPES

# Load the environment variables from .env file
load_dotenv()

# Define the MQTT broker details
mqtt_username = os.getenv("MQTT_USERNAME")
mqtt_password = os.getenv("MQTT_PASSWORD")
broker_address = os.getenv("MQTT_BROKER_ADDRESS")
broker_port = int(os.getenv("MQTT_BROKER_PORT"))

client = mqtt.Client()
client.username_pw_set(mqtt_username, mqtt_password)

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT Broker!")
    else:
        print(f"Failed to connect, return code {rc}")

client.on_connect = on_connect

def send_mqtt_message(mqtt_topic, mqtt_message):
    client.connect(broker_address, broker_port)

    client.publish(mqtt_topic, mqtt_message)

    client.disconnect()

    return True

def send_trigger_message(trigger_type):
    mqtt_topic = "gate/trigger"

    if (trigger_type in map(lambda x: x[0], TRIGGER_TYPES)):
        send_mqtt_message(mqtt_topic, trigger_type)
        return True

    return False