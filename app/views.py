from .mqtt_publisher import send_mqtt_message
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

class IndexView(APIView):
    def get(self, request):
        return Response({'message': 'Hello, World!'}, status=status.HTTP_200_OK)
    
class GateVehicleTrigger(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        send_mqtt_message("gate/start/vehicle/test") # Change the topic in production to "gate/start/vehicle"
        return Response({'message': ''}, status=status.HTTP_200_OK)
    
class GatePedestrianTrigger(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        send_mqtt_message("gate/start/pedestrian/test") # Change the topic in production to "gate/start/pedestrian"
        return Response({'message': ''}, status=status.HTTP_200_OK)

 