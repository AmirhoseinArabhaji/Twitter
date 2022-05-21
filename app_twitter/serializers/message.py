from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils.translation import gettext as _
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from app_twitter.models import Message, Conversation
from app_twitter.serializers.profile import AuthorSerializer

User = get_user_model()


class MessageSerializer(serializers.ModelSerializer):
    contact = serializers.CharField(required=True, write_only=True)
    author = AuthorSerializer(read_only=True)
    body = serializers.CharField(required=True, allow_null=False, allow_blank=False)

    class Meta:
        model = Message
        fields = (
            'id',
            'author',
            'contact',
            'body',
            'seen',
            'created_at',
        )

        read_only_fields = (
            'id',
            'created_at',
            'author',
            'seen',
        )

    def validate(self, attrs):
        attrs = super().validate(attrs)

        username = attrs['contact']

        user = User.objects.filter(username=username)
        if not user.exists():
            raise ValidationError({'message': _('user with this username does not exists')})

        attrs['contact'] = user.first()

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        message = self.Meta.model.objects.create(
            author=self.context['request'].user,
            body=validated_data['body'],
            contact=validated_data['contact']
        )

        return message


class ConversationSerializer(serializers.ModelSerializer):
    participant = serializers.SerializerMethodField(read_only=True)
    last_message = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Conversation
        fields = (
            'id',
            'participant',
            'last_message',
            'updated_at',
        )

    @staticmethod
    def get_last_message(instance: Conversation):
        message = instance.messages.first()
        body = message.body[:20]
        if not body == message.body:
            body += ' ...'
        return body

    def get_participant(self, instance: Conversation):
        user = self.context['request'].user
        starter = instance.starter_participant
        contact = instance.contact_participant
        return AuthorSerializer(instance=contact if starter == user else starter, context=self.context).data


class ReadingMessageSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(required=True, write_only=True)
    read_from = serializers.DateTimeField(required=False)
    to_date = serializers.DateTimeField(required=False)

    class Meta:
        model = Message
        fields = (
            'id',
            'read_from',
            'to_date',
        )

    def update(self, instance: Message, validated_data):
        instance.seen = True
        instance.save()

        return instance

    def create(self, validated_data):
        pass


__all__ = [
    'MessageSerializer',
    'ConversationSerializer',
    'ReadingMessageSerializer',
]
