import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.urls import path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pharma_web.settings')

django_asgi_app = get_asgi_application()

try:
	from chat.routing import websocket_urlpatterns
except Exception:
	websocket_urlpatterns = []

application = ProtocolTypeRouter({
	"http": django_asgi_app,
	"websocket": AuthMiddlewareStack(
		URLRouter(websocket_urlpatterns)
	),
})
