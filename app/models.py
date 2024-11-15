from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

TRIGGER_AGENTS = (
    ('api', 'Triggered by API'),
    ('rpi', 'Triggered by RPI'),
    ('manual', 'Triggered Manually'),
)

TRIGGER_TYPES = (
    ('start_v', 'Start opening Vehicle'),
    ('stop', 'Stop opening'),
    ('start_p', 'Start opening Pedestrian'),
)

GATE_STATES = (
    ('open_p', 'Open Pedestrian'),
    ('open_v', 'Open Vehicle'),
    ('closed', 'Closed'),
    ('not_closed', 'Not Closed')
)

class GateStateHistory(models.Model):
    gate_state = models.CharField(max_length=20, choices=GATE_STATES)
    trigger = models.ForeignKey('TriggerHistory', on_delete=models.CASCADE, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.gate_state

class TriggerHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    trigger_agent = models.CharField(max_length=20, choices=TRIGGER_AGENTS)
    trigger_type = models.CharField(max_length=20, choices=TRIGGER_TYPES)

    timestamp = models.DateTimeField(auto_now_add=True)
 
    @classmethod
    def get_trigger(cls):
        trigger = cls.objects.filter(timestamp__gte=timezone.now() - timedelta(seconds=10)).last()
        if trigger:
            return trigger
        return None

    def __str__(self):
        return f"{self.user.username} - {self.trigger_agent} - {self.trigger_type}"