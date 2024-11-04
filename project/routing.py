from django.urls import re_path
from .consumers import *

websocket_urlpatterns = [
    re_path(r'ws/gate/status/$', GateStatusConsumer.as_asgi()),
    re_path(r'ws/gate/trigger/$', GateTriggerConsumer.as_asgi()),
]