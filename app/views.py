from .mqtt_publisher import send_trigger_message
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from .models import *

class IndexView(APIView):
    def get(self, request):
        return Response({'message': 'Hello, World!'}, status=status.HTTP_200_OK)
    
class GateTrigger(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        trigger_type = request.data.get('trigger_type')

        if not trigger_type:
            return Response({'error': 'Please provide a trigger_type'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            if not send_trigger_message(trigger_type):
                return Response({'error': 'Invalid trigger type'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(e)
            return Response({'error': 'Failed to send trigger'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        TriggerHistory.objects.create(user=request.user, trigger_agent='api', trigger_type=trigger_type)

        return Response({'message': 'Success'}, status=status.HTTP_200_OK)

