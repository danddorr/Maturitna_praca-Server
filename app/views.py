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
        if gate_state is None:
            gate_state = "unknown" 

        user_data = {
            "username": request.user.username,
            "is_admin": request.user.is_admin,
            "can_open_vehicle": request.user.can_open_vehicle,
            "can_open_pedestrian": request.user.can_open_pedestrian,
            "can_close_gate": request.user.can_close_gate
        }

        data = {
            "gate_state": gate_state,
            "user": user_data
        }

        return Response(data, status=status.HTTP_200_OK)
    
class TemporaryAccessView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        access = TemporaryAccess.objects.filter(user=user)
        serializer = TemporaryAccessSerializer(access, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request, *args, **kwargs):
        serializer = TemporaryAccessSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
class TemporaryAccessDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, link):
        access = TemporaryAccess.objects.filter(link=link).first()
        if access:
            serializer = TemporaryAccessSerializer(access, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response({'message': 'Temporary access not found'}, status=status.HTTP_404_NOT_FOUND)
    
    def delete(self, request, link):
        access = TemporaryAccess.objects.filter(link=link).first()
        if access:
            access.delete()
            return Response({'message': 'Temporary access deleted'}, status=status.HTTP_200_OK)
        return Response({'message': 'Temporary access not found'}, status=status.HTTP_404_NOT_FOUND)
    
    def patch(self, request, link):
        access = TemporaryAccess.objects.filter(link=link).first()
        if access:
            serializer = TemporaryAccessSerializer(access, data=request.data, partial=True, context={'request': request})
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response({'message': 'Temporary access not found'}, status=status.HTTP_404_NOT_FOUND)
    
    def put(self, request, link):
        access = TemporaryAccess.objects.filter(link=link).first()
        if access:
            serializer = TemporaryAccessSerializer(access, data=request.data, context={'request': request})
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response({'message': 'Temporary access not found'}, status=status.HTTP_404_NOT_FOUND)
     