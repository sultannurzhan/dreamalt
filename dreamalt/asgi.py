import os
import django

# ✅ Set settings before importing anything Django-related
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dreamalt.settings')

# ✅ Set up Django BEFORE anything else
django.setup()

# ✅ Import routing *AFTER* setup
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import base.routing  # now safe

from django.core.asgi import get_asgi_application

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            base.routing.websocket_urlpatterns
        )
    ),
})