# serializers.py
from rest_framework import serializers
from django.utils import timezone
from .models import TemporaryAccess, RegisteredECV, CustomUser
import secrets

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['username', 'is_admin', 'can_open_vehicle', 'can_open_pedestrian', 'can_close_gate']

class TemporaryAccessSerializer(serializers.Serializer):  
    access_type = serializers.CharField()
    ecv = serializers.CharField(required=False)
    valid_from = serializers.DateTimeField()
    valid_until = serializers.DateTimeField()
    open_vehicle = serializers.IntegerField()
    open_pedestrian = serializers.IntegerField()
    close_gate = serializers.IntegerField()

    def validate(self, data):        
        errors = {}

        if data.get('access_type') == "ecv" and not data.get('ecv'):
            errors['ecv'] = "ECV is required"
        
        user = self.context['request'].user
        if data.get('open_vehicle') == -1 or data.get('open_pedestrian') == -1 or data.get('close_gate') == -1:
            if not user.is_admin:
                errors['open_vehicle'] = "User does not have permission to grant unlimited access"
                errors['open_pedestrian'] = "User does not have permission to grant unlimited access"
                errors['close_gate'] = "User does not have permission to grant unlimited access"

        if data.get('open_vehicle') > 10:
            errors['open_vehicle'] = "Maximum value for opening gate for vehicle is 10"
        if data.get('open_pedestrian') > 10:
            errors['open_pedestrian'] = "Maximum value for opening gate for pedestrian is 10"
        if data.get('close_gate') > 10:
            errors['close_gate'] = "Maximum value for closing gate is 10"

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
        return secrets.token_urlsafe(12) 

    def create(self, validated_data):
        link = self.generate_link()

        user = self.context['request'].user

        if validated_data.get('access_type') == "ecv":
            ecv = RegisteredECV.objects.filter(ecv=validated_data['ecv']).first()
            if ecv and ecv.user != user:
                raise serializers.ValidationError({"ecv": "This ECV is registered by another user"})
            
            if TemporaryAccess.objects.filter(user=user, ecv=validated_data['ecv']).exists():
                raise serializers.ValidationError({"ecv": "Temporary access for this ECV already exists"})
            
        if validated_data.get('open_vehicle') and not user.can_open_vehicle:
            raise serializers.ValidationError({"open_vehicle": "You do not have permission to grant open vehicle gate access"})
        if validated_data.get('open_pedestrian') and not user.can_open_pedestrian:
            raise serializers.ValidationError({"open_pedestrian": "You do not have permission to grant open pedestrian gate access"})
        if validated_data.get('close_gate') and not user.can_close_gate:
            raise serializers.ValidationError({"close_gate": "You do not have permission to grant close gate access"})
        
        return TemporaryAccess.objects.create(
            user=user,
            ecv=validated_data.get('ecv', None),
            link=link,
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
    
    def get_status(self, instance):
        if instance.valid_from > timezone.now():
            return "Pending"
        if instance.valid_until < timezone.now():
            return "Expired"
        if instance.open_vehicle == 0 and instance.open_pedestrian == 0 and instance.close_gate == 0:
            return "Revoked"
        return "Active"
    
    def to_representation(self, instance): #converts the instance to a dictionary
        return {
            "access_type": "ecv" if instance.ecv else "link",
            "link": instance.link,
            "ecv": instance.ecv if instance.ecv else None,
            "valid_from": instance.valid_from,
            "valid_until": instance.valid_until,
            "open_vehicle": instance.open_vehicle,
            "open_pedestrian": instance.open_pedestrian,
            "close_gate": instance.close_gate,
            "status": self.get_status(instance)
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