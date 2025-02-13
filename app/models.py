from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from datetime import timedelta
from django.conf import settings

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

CAMERA_POSITIONS = (
    ('outside', 'Outside camera'),
    ('inside', 'Inside camera')
)

class CustomUser(AbstractUser):
    is_admin = models.BooleanField(default=False)
    can_open_vehicle = models.BooleanField(default=False)
    can_open_pedestrian = models.BooleanField(default=False)
    can_close_gate = models.BooleanField(default=False)

    special_token = models.CharField(max_length=64, null=True, blank=True)

    def has_permission(self, trigger_type):
        if trigger_type == 'start_v':
            return self.can_open_vehicle
        elif trigger_type == 'start_p':
            return self.can_open_pedestrian
        elif trigger_type == 'stop':
            return self.can_close_gate
        return False

    def __str__(self):
        return f"{self.username}"


class GateStateLog(models.Model):
    gate_state = models.CharField(max_length=20, choices=GATE_STATES)
    trigger = models.ForeignKey('TriggerLog', on_delete=models.CASCADE, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.gate_state

class TriggerLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True)
    ecv = models.ForeignKey('RegisteredECV', on_delete=models.CASCADE, null=True)
    trigger_agent = models.CharField(max_length=20, choices=TRIGGER_AGENTS)
    trigger_type = models.CharField(max_length=20, choices=TRIGGER_TYPES)
    camera_position = models.CharField(max_length=50, choices=CAMERA_POSITIONS, null=True)

    timestamp = models.DateTimeField(auto_now_add=True)
 
    @classmethod
    def get_trigger(cls):
        trigger = cls.objects.filter(timestamp__gte=timezone.now() - timedelta(seconds=10)).last()
        if trigger:
            return trigger
        return None

    def __str__(self):
        return f"{self.user.username} - {self.trigger_agent} - {self.trigger_type}"
    
class RegisteredECV(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True)
    ecv = models.CharField(max_length=10, unique=True)
    is_allowed = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.ecv}"
    
class ParkedVehicle(models.Model):
    ecv = models.ForeignKey('RegisteredECV', on_delete=models.CASCADE)
    entered_at = models.DateTimeField(auto_now_add=True)
    exited_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.ecv}"

class TemporaryAccess(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    ecv = models.CharField(max_length=10, null=True)
    link = models.CharField(max_length=32, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    valid_from = models.DateTimeField(null=True)
    valid_until = models.DateTimeField(null=True)
    
    open_vehicle = models.IntegerField(default=0) #-1 means unlimited
    open_pedestrian = models.IntegerField(default=0)
    close_gate = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.user.username}"