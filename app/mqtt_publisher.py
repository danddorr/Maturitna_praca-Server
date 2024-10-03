import os
from dotenv import load_dotenv
import paho.mqtt.client as mqtt

# Load the environment variables from .env file
load_dotenv()

# Define the MQTT broker details
mqtt_username = os.getenv("MQTT_USERNAME")
mqtt_password = os.getenv("MQTT_PASSWORD")
broker_address = os.getenv("MQTT_BROKER_ADDRESS")
broker_port = int(os.getenv("MQTT_BROKER_PORT"))

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT Broker!")
    else:
        print(f"Failed to connect, return code {rc}")

def send_mqtt_message(mqtt_topic):
    # Create an MQTT client instance
    client = mqtt.Client()
    client.username_pw_set(mqtt_username, mqtt_password)

    client.on_connect = on_connect

    # Connect to the MQTT broker
    client.connect(broker_address, broker_port)

    # Publish the message 1 to the specified topic
    client.publish(mqtt_topic, 1)
    
    # Disconnect from the MQTT broker
    client.disconnect()

    return True

 