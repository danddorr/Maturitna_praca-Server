from django.urls import path
from .views import *

urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    path('general-info/', GeneralInfoView.as_view(), name='general-info'),
]
