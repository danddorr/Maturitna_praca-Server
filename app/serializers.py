# serializers.py
from rest_framework import serializers
from .models import TemporaryAccess, RegisteredECV, CustomUser
import secrets

class PermissionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['is_admin', 'can_open_vehicle', 'can_open_pedestrian', 'can_close_gate']

class GeneralInfoSerializer(serializers.Serializer):
    gate_state = serializers.CharField()
    permissions = PermissionsSerializer(source='*')

class TemporaryAccessCreateSerializer(serializers.Serializer):  
    access_type = serializers.CharField()
    ecv = serializers.CharField(required=False)
    valid_from = serializers.DateTimeField()
    valid_until = serializers.DateTimeField()
    open_vehicle = serializers.IntegerField()
    open_pedestrian = serializers.IntegerField()
    close_gate = serializers.IntegerField()

    def validate(self, data):
        if data.get('access_type') == "link":
            data['link'] = self.generate_link()
        
        errors = {}

        if data.get('access_type') == "ecv" and not data.get('ecv'):
            errors['ecv'] = "ECV is required"
        
        user = self.context['request'].user
        if data.get('open_vehicle') and not user.can_open_vehicle:
            errors['open_vehicle'] = "User does not have permission to open vehicle gate"
        if data.get('open_pedestrian') and not user.can_open_pedestrian:
            errors['open_pedestrian'] = "User does not have permission to open pedestrian gate"
        if data.get('close_gate') and not user.can_close_gate:
            errors['close_gate'] = "User does not have permission to close gate"

        if errors:
            raise serializers.ValidationError(errors)

        return data
    
    def generate_link(self):
        return secrets.token_urlsafe(24) 

    def create(self, validated_data):
        user = self.context['request'].user
        ecv = None
        if validated_data.get('access_type') == "ecv":
            ecv = RegisteredECV.objects.get(ecv=validated_data['ecv'])
        
        return TemporaryAccess.objects.create(
            user=user,
            ecv=ecv,
            link=validated_data.get('link'),
            valid_from=validated_data['valid_from'],
            valid_until=validated_data['valid_until'],
            open_vehicle=validated_data['open_vehicle'],
            open_pedestrian=validated_data['open_pedestrian'],
            close_gate=validated_data['close_gate']
        )
    
    def update(self, instance, validated_data):
        instance.valid_from = validated_data.get('valid_from', instance.valid_from)
        instance.valid_until = validated_data.get('valid_until', instance.valid_until)
        instance.open_vehicle = validated_data.get('open_vehicle', instance.open_vehicle)
        instance.open_pedestrian = validated_data.get('open_pedestrian', instance.open_pedestrian)
        instance.close_gate = validated_data.get('close_gate', instance.close_gate)
        instance.save()
        return instance
    
    def to_representation(self, instance): #converts the instance to a dictionary
        return {
            "link": instance.link,
            "ecv": instance.ecv.ecv if instance.ecv else None,
            "valid_from": instance.valid_from,
            "valid_until": instance.valid_until,
            "open_vehicle": instance.open_vehicle,
            "open_pedestrian": instance.open_pedestrian,
            "close_gate": instance.close_gate
        }
    #dummy json
    """
    {
        "access_type": "link",
        "valid_from": "2024-07-10T00:00:00Z",
        "valid_until": "2025-07-10T23:59:59Z",
        "open_vehicle": 1,
        "open_pedestrian": 1,
        "close_gate": 1
    }

    {
        "access_type": "ecv",
        "ecv": "TT350HO",
        "valid_from": "2024-07-10T00:00:00Z",
        "valid_until": "2025-07-10T23:59:59Z",
        "open_vehicle": 1,
        "open_pedestrian": 1,
        "close_gate": 1
    }
    """