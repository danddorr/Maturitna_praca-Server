from rest_framework.response import Response
from rest_framework import status, generics, viewsets
from rest_framework.views import APIView
from .models import *
from django.core.cache import cache
from rest_framework.permissions import IsAuthenticated
from .permissions import IsOwner
from .serializers import *
from datetime import datetime, timedelta

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
    def get_permissions(self):
        if self.request.method == "GET":
            return []
        return [IsAuthenticated(), IsOwner()]

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

class UserTriggerLogView(generics.ListAPIView):
    serializer_class = TriggerLogSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return TriggerLog.objects.filter(user=self.request.user).order_by('-timestamp')

class GateStateLogView(generics.ListAPIView):
    serializer_class = GateStateLogSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return GateStateLog.objects.exclude(state="not_closed").order_by('-timestamp')

class ParkedVehicleListView(generics.ListAPIView):
    serializer_class = ParkedVehicleSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None
    
    def get_queryset(self):
        return ParkedVehicle.objects.filter(exited_at=None).order_by('entered_at')

class ParkingStatisticsView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        # Get current date and 7 days ago date
        today = timezone.now().date()
        week_ago = today - timedelta(days=6)  # 7 days including today
        
        # Count current parked vehicles
        current_parked = ParkedVehicle.objects.filter(exited_at=None).count()
        
        # Initialize daily stats dictionary
        daily_stats = {}
        for i in range(7):
            day = week_ago + timedelta(days=i)
            daily_stats[day.strftime('%Y-%m-%d')] = 0
        
        # Calculate daily parked vehicles
        for day_str in daily_stats.keys():
            day_date = datetime.strptime(day_str, '%Y-%m-%d').date()
            next_day = day_date + timedelta(days=1)
            
            # Count vehicles that entered on that day
            count = ParkedVehicle.objects.filter(
                entered_at__date=day_date
            ).count()
            
            daily_stats[day_str] = count
        
        data = {
            'current_parked': current_parked,
            'daily_stats': daily_stats
        }
        
        return Response(data, status=status.HTTP_200_OK)

class RegisteredECVViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing registered license plates (ECVs)
    """
    serializer_class = RegisteredECVSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Returns only ECVs belonging to the current user"""
        return RegisteredECV.objects.filter(user=self.request.user).order_by('-created_at')
