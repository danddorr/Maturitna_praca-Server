from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from .models import *
from django.core.cache import cache
from rest_framework.permissions import IsAuthenticated
from .serializers import *

class IndexView(APIView):
    def get(self, request):
        return Response({'message': 'Hello, World!'}, status=status.HTTP_200_OK)
    
class GeneralInfoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        gate_state = cache.get("gate_state")

        data = {
            "gate_state": gate_state,
            "is_admin": request.user.is_admin,
            "can_open_vehicle": request.user.can_open_vehicle,
            "can_open_pedestrian": request.user.can_open_pedestrian,
            "can_close_gate": request.user.can_close_gate
        }

        serializer = GeneralInfoSerializer(data=data)
        if serializer.is_valid():
            return Response(serializer.data)
        return Response(serializer.errors, status=400)
        