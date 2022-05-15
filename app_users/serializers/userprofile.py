from django.contrib.auth import get_user_model
from django.utils.translation import gettext as _
from rest_framework import serializers

from utilities.serializers import HybridImageField

User = get_user_model()


class UserProfileSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = User
        fields = (
            'avatar',
            'fullname',
            'phone',
            'username',
            'email',
            'date_joined',
        )

        read_only_fields = ('phone', 'username', 'email', 'date_joined')

    def to_representation(self, instance):
        avatar = HybridImageField(use_url=True)

        result = super().to_representation(instance)

        result.update({
            'avatar': avatar.to_representation(file=instance.avatar),
        })

        request = self.context.get('request', None)

        if request:
            if request.user.is_authenticated:
                result['is_ban'] = instance.is_ban

        return result


class UserMetadataSerializer(serializers.Serializer):
    AppTypes = (
        ('WEB', _('web app')),
        ('ANDROID', _('android app')),
        ('IOS', _('ios app')),
    )

    registration_app = serializers.ChoiceField(choices=AppTypes, required=False)

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass
