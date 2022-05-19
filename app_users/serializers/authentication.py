from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils.translation import gettext as _
from rest_framework import exceptions, serializers
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.tokens import RefreshToken

from app_users.backends import PasswordAuthenticationBackend
from app_users.serializers.userprofile import UserMetadataSerializer
from utilities.validators import phone_number_validator

User = get_user_model()


class UserLoginSerializer(serializers.ModelSerializer):
    phone = serializers.CharField(max_length=11, write_only=True, required=False, allow_null=False,
                                  validators=[phone_number_validator])

    email = serializers.EmailField(write_only=True, required=False, allow_null=True)

    username = serializers.CharField(write_only=True, required=False, allow_null=True)

    password = serializers.CharField(required=True)

    metadata = UserMetadataSerializer(write_only=True, required=False)

    class Meta:
        model = User
        fields = (
            'phone',
            'email',
            'username',
            'password',
            'metadata',
        )

    def validate(self, attrs):
        return attrs


class UserRegisterSerializer(serializers.HyperlinkedModelSerializer):
    username = serializers.CharField(write_only=True, required=True)

    phone = serializers.CharField(max_length=11, write_only=True, required=False, allow_null=True,
                                  validators=[phone_number_validator])

    email = serializers.EmailField(write_only=True, required=False)

    password = serializers.CharField(style={'input_type': 'password'}, min_length=6, write_only=True, required=True,
                                     allow_null=False)

    metadata = UserMetadataSerializer(write_only=True, required=False)

    class Meta:
        model = User
        fields = (
            'username',
            'phone',
            'email',
            'password',
            'metadata',
        )

    def validate(self, attrs):
        attrs = super().validate(attrs)

        username = attrs.get('username')
        phone_number = attrs.get('phone')
        email = attrs.get('email')

        if not phone_number or not email:
            raise ValidationError({'message': _('email or phone number is required')})

        if User.objects.filter(username=username).exists():
            raise ValidationError({'message': _('User with this username exists!')})

        if phone_number and User.objects.filter(phone=phone_number).exists():
            raise ValidationError({'message': _('Phone number does exist!')})

        if email and User.objects.filter(email=email).exists():
            raise ValidationError({'message': _('Email does exist!')})

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        user_obj = User(**validated_data)
        user_obj.set_password(validated_data.get('password'))
        user_obj.save()

        return user_obj


class BaseTokenAuthenticationSerializer(serializers.Serializer):
    username = serializers.CharField(required=False, write_only=True)

    phone = serializers.CharField(max_length=11, required=False, write_only=True, validators=[phone_number_validator])

    email = serializers.EmailField(required=False, write_only=True)
    password = serializers.CharField(min_length=6, required=True, write_only=True)

    class Meta:
        fields = (
            'username'
            'email',
            'phone',
            'password',
        )

    def validate(self, attrs):
        attrs = super().validate(attrs)

        if not attrs.get('username') and not attrs.get('email') and not attrs.get('phone'):
            raise ValidationError({"message": _("username or email or phone is required for login")})

        if not attrs.get('password'):
            raise ValidationError({"password": _("password is required for the login")})

        return attrs

    @classmethod
    def get_token(cls, user):
        token = RefreshToken.for_user(user)
        token['user_id'] = user.id
        token['fullname'] = user.fullname
        token['phone'] = user.phone
        token['username'] = user.username

        return {
            'access': str(token.access_token),
            'refresh': str(token),
        }

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class DefaultTokenObtainPairSerializer(BaseTokenAuthenticationSerializer):

    def validate(self, attrs):
        attrs = super().validate(attrs)

        custom_backend = PasswordAuthenticationBackend()
        user = custom_backend.authenticate(request=self.context['request'], **attrs)

        if user is None or not user.is_active:
            raise exceptions.AuthenticationFailed({'message': _('No active account found with the given credentials')})

        return self.get_token(user)


class AdminTokenObtainPairSerializer(BaseTokenAuthenticationSerializer):
    class Meta(BaseTokenAuthenticationSerializer.Meta):
        exclude = ('token',)

    def validate(self, attrs):
        attrs = super().validate(attrs)

        custom_backend = PasswordAuthenticationBackend()
        user = custom_backend.authenticate(request=self.context['request'], **attrs)

        if not user:
            raise exceptions.AuthenticationFailed({'message': _('No admin account found with the given credentials')})

        if not user.is_staff:
            raise exceptions.AuthenticationFailed(
                {'message': _('No admin account found with the given credentials')})

        return self.get_token(user)

# TODO Forgot password, reset password
