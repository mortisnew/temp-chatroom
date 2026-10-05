import os

os.environ.setdefault(
    'DJANGO_SETTINGS_MODULE',
    'config.settings'
)

from django.core.asgi import get_asgi_application
from django.contrib.staticfiles.handlers import ASGIStaticFilesHandler

from channels.routing import ProtocolTypeRouter, URLRouter

django_asgi_app = get_asgi_application()

from chat.routing import websocket_urlpatterns


application = ProtocolTypeRouter({

    'http': ASGIStaticFilesHandler(
        django_asgi_app
    ),

    'websocket': URLRouter(
        websocket_urlpatterns
    ),
})