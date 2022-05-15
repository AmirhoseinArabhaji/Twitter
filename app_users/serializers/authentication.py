from django.conf import settings
from django.db import transaction
from django.utils.translation import gettext as _
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from app_users.models import User
from app_users.serializers.userprofile import UserMetadataSerializer
from utilities.validators import phone_number_validator


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

    password = serializers.CharField(style={'input_type': 'password'}, min_length=20, write_only=True, required=True,
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
        attrs = super(UserRegisterSerializer, self).validate(attrs)

        phone_number = attrs.get('phone')
        email = attrs.get('email')

        if User.objects.filter(phone=phone_number).exists():
            raise ValidationError({"message": _("Phone number does exist!")})

        if email and User.objects.filter(email=email).exists():
            raise ValidationError({"message": _("Email does exist!")})
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        user_obj = User(**validated_data)
        user_obj.set_password(validated_data.get('password'))
        user_obj.save()

        return user_obj

# TODO Forgot password, reset password
