from django.urls import path, include
from rest_framework.routers import DefaultRouter
from app_twitter.management.views import *

router = DefaultRouter()
router.register('tweets', AdminTwitterManagementViewSet)
router.register('hashtags', AdminHashtagManagementViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
