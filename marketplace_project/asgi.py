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
from channels.security.websocket import AllowedHostsOriginValidator
import marketplace_app.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'marketplace_project.settings')

# Initialize Django ASGI application early for model imports
django_asgi_app = get_asgi_application()

# Define ASGI application that supports HTTP and WebSocket
application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(marketplace_app.routing.websocket_urlpatterns)
        )
    ),
})
