from django.urls import path

from app_twitter.statistics.views import *

urlpatterns = [
    path('', twitter_statistics),
]
