from django.urls import re_path
from .consumers import *

websocket_urlpatterns = [
    re_path(r'ws/gate/status/$', MyConsumer.as_asgi()),
    re_path(r'ws/secret/gate/status/$', MyConsumer.as_asgi()),
]