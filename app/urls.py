from django.urls import path
from .views import *

urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    path('general-info/', GeneralInfoView.as_view(), name='general-info'),
    path('temporary-access/', TemporaryAccessView.as_view(), name='temporary-access'),
    path('temporary-access/<str:link>/', TemporaryAccessDetailView.as_view(), name='temporary-access-detail'),
    path('triggers/', UserTriggerLogView.as_view(), name='triggers'),
    path('states/', GateStateLogView.as_view(), name='states'),
]
