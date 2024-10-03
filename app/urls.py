from django.urls import path
from .views import *

urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    path('vehicle', GateVehicleTrigger.as_view(), name='vehicle'),
    path('pedestrian', GatePedestrianTrigger.as_view(), name='pedestrian'),
]
