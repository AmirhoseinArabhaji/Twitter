from django.urls import path

from app_notification.views import *

app_name = 'app_notification'

urlpatterns = [
    path('read/', read_notification, name='read_notification'),
]
