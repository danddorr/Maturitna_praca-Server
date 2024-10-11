from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Starts the MQTT listener to receive gate status updates.'

    def handle(self, *args, **kwargs):
        from app.mqtt_listener import start_mqtt_listener
        start_mqtt_listener()