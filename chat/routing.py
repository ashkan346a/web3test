from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r"^ws/chat/user/$", consumers.UserChatConsumer.as_asgi()),
    re_path(r"^ws/chat/agent/(?P<room_id>\d+)/$", consumers.AgentChatConsumer.as_asgi()),
    re_path(r"^ws/chat/agent-feed/$", consumers.AgentFeedConsumer.as_asgi()),
]
