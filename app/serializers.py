# serializers.py
from rest_framework import serializers
from .models import CustomUser

class PermissionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['is_admin', 'can_open_vehicle', 'can_open_pedestrian', 'can_close_gate']

class GeneralInfoSerializer(serializers.Serializer):
    gate_state = serializers.CharField()
    permissions = PermissionsSerializer(source='*')