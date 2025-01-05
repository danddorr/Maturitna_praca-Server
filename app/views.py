from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from .models import *
from django.core.cache import cache

class IndexView(APIView):
    def get(self, request):
        return Response({'message': 'Hello, World!'}, status=status.HTTP_200_OK)
    
class GateStateView(APIView):
    def get(self, request):
        gate_state = cache.get("gate_state")
        
        return Response({'type':'status', 'message': gate_state}, status=status.HTTP_200_OK)
    