from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'yolov8/ws/stream/(?P<stream_id>\w+)/$', consumers.StreamConsumer.as_asgi()),
]
