from django.urls import path
from .views import *

urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    path('trigger/', GateTrigger.as_view(), name='trigger'),
]
