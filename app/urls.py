from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *

# Create a router and register our viewsets with it
router = DefaultRouter()
router.register('license-plates', RegisteredECVViewSet, basename='license-plates')

urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    path('general-info/', GeneralInfoView.as_view(), name='general-info'),
    path('temporary-access/', TemporaryAccessView.as_view(), name='temporary-access'),
    path('temporary-access/<str:link>/', TemporaryAccessDetailView.as_view(), name='temporary-access-detail'),
    path('triggers/', UserTriggerLogView.as_view(), name='triggers'),
    path('states/', GateStateLogView.as_view(), name='states'),
    path('parking/', ParkedVehicleListView.as_view(), name='parked-vehicles'),
    path('parking/statistics/', ParkingStatisticsView.as_view(), name='parking-statistics'),
    
    # Include the router URLs
    path('', include(router.urls)), 
]
