

from django.urls import include, path
from rest_framework import routers

from . import views


router = routers.DefaultRouter()

router.register(r'chat', views.ChatViewSet, basename='chat')
router.register(r'message', views.MessageViewSet, basename='message')
router.register(r'nicknames', views.NickNameViewSet, basename='nickname')


urlpatterns = [
    path('', views.home, name='home'),
    path('room/<str:room_code>/',views.room, name='room'),
    path('api/', include(router.urls)),
]