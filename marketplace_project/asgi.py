"""
ASGI config for marketplace_project project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import marketplace_app.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'marketplace_project.settings')

# Define ASGI application that supports HTTP and WebSocket
application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            marketplace_app.routing.websocket_urlpatterns
        )
    ),
})
