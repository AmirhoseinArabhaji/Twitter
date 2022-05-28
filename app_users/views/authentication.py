from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from rest_framework import generics, status
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenViewBase
from utilities.mixins import LazyAuthenticationMixin

from app_users.serializers import authentication
from app_users.serializers.authentication import *

User = get_user_model()


class UserLoginAPIView(LazyAuthenticationMixin, generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = authentication.UserLoginSerializer
    permission_classes = (AllowAny,)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data.get('email')
        phone = serializer.validated_data.get('phone')
        username = serializer.validated_data.get('username')

        with transaction.atomic():
            user = User.objects.get(Q(email=email) | Q(phone=phone) | Q(username=username))

        if user.is_ban:
            raise AuthenticationFailed(_('User is ban'), code='user_banned')

        refresh = RefreshToken.for_user(user)

        return Response(status=status.HTTP_200_OK, data={
            "message": _("Now your account is active"),
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        })


class UserRegisterAPIView(LazyAuthenticationMixin, generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = authentication.UserRegisterSerializer
    permission_classes = (AllowAny,)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(status=status.HTTP_200_OK, data={"message": _("You registered successfully!")})


class UserActivationAPIView(generics.UpdateAPIView):
    queryset = User.objects.all()
    # serializer_class = authentication.ActivationTokenSerializer
    permission_classes = (AllowAny,)

    def patch(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        serializer.update(instance=None, validated_data=serializer.validated_data)

        user = User.objects.get(phone=serializer.validated_data.get("phone"))
        refresh = RefreshToken.for_user(user)

        return Response(status=status.HTTP_200_OK, data={
            "message": _("Now your account is active"),
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        })


class CustomTokenObtainPairView(TokenViewBase):
    serializer_class = DefaultTokenObtainPairSerializer


class AdminTokenObtainPairView(TokenViewBase):
    serializer_class = AdminTokenObtainPairSerializer
