from django.urls import path, include

from .views.authentication import UserRegisterAPIView, CustomTokenObtainPairView, AdminTokenObtainPairSerializer

app_name = 'app_users'

urlpatterns = [
    path('register/', UserRegisterAPIView.as_view()),
    path('login/', CustomTokenObtainPairView.as_view()),
    path('admin_login/', CustomTokenObtainPairView.as_view()),
]
