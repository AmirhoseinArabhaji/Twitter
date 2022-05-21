from datetime import datetime

from django.db.models import Q
from django.utils.http import parse_http_date_safe
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.generics import CreateAPIView, UpdateAPIView, get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet

from app_notification.models import Notification
from app_twitter import permissions
from app_twitter.models import Message, Conversation, MessagesInConversation
from app_twitter.permissions import IsAMessageContact, IsPartOfConversation
from app_twitter.serializers.message import *
from app_twitter.tasks.notifications import notify


class SendPrivateMessageAPIView(CreateAPIView):
    queryset = Message.objects.none()
    serializer_class = MessageSerializer
    permission_classes = (IsAuthenticated, permissions.UsernameIsActive)

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        message = serializer.create(validated_data=serializer.validated_data)

        receiver = serializer.validated_data.get('contact', None)

        conversation = Conversation.objects.filter(Q(contact_participant=receiver) | Q(starter_participant=receiver))

        if conversation.exists():
            conversation = conversation.first()
        else:
            conversation = Conversation.objects.create(starter_participant=request.user,
                                                       contact_participant=receiver)

        conversation.messages.add(message)  # noqa
        conversation.save()

        notify(instance=conversation,
               to=receiver,
               by=request.user,
               _type=Notification.NotificationsTypes.MESSAGE)

        return Response(status=status.HTTP_200_OK, data={
            'id': conversation.id,
            'message': MessageSerializer(message).data,
        })


class ConversationAPIView(ReadOnlyModelViewSet):
    queryset = Conversation.objects.all()
    serializer_class = ConversationSerializer
    permission_classes = (IsAuthenticated,)
    lookup_field = 'pk'

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Conversation.objects.none()

        user = self.request.user
        return super().get_queryset().filter(Q(contact_participant=user) | Q(starter_participant=user)).cache()

    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated, permissions.IsPartOfConversation])
    def messages(self, request, *args, **kwargs):
        conversation = self.get_object()
        messages = conversation.messages.all()

        before = self.request.query_params.get('before', None)
        before = before and parse_http_date_safe(before)
        if before:
            dt = datetime.fromtimestamp(before)
            messages = messages.filter(created_at__lte=dt)

        if_modified_since = self.request.META.get('HTTP_IF_MODIFIED_SINCE')
        if_modified_since = if_modified_since and parse_http_date_safe(if_modified_since)

        if if_modified_since:
            dt = datetime.fromtimestamp(if_modified_since)
            messages = messages.filter(created_at__gte=dt)

        page = self.paginate_queryset(messages)
        if page is not None:
            serializer = MessageSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)


class ReadMessageView(UpdateAPIView):
    queryset = Message.objects.all().cache()
    serializer_class = ReadingMessageSerializer
    permission_classes = (IsAMessageContact,)
    lookup_field = 'pk'

    http_method_names = ('patch',)

    def get_object(self):
        serializer = self.get_serializer(data=self.request.data)
        serializer.is_valid(raise_exception=True)
        instance = get_object_or_404(self.get_queryset(), pk=serializer.validated_data['id'])
        self.check_object_permissions(request=self.request, obj=instance)

        return instance


class ReadingConversationMessages(UpdateAPIView):
    queryset = Conversation.objects.all().cache()
    serializer_class = ReadingMessageSerializer
    permission_classes = (IsPartOfConversation,)
    lookup_field = 'pk'

    http_method_names = ('patch',)

    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=self.request.data)
        serializer.is_valid(raise_exception=True)

        pk = serializer.validated_data['id']
        from_date = serializer.validated_data.get('from_date', None)
        to_date = serializer.validated_data.get('to_date', None)

        instance = get_object_or_404(self.get_queryset(), pk=pk)
        self.check_object_permissions(request=self.request, obj=instance)

        messages_conversations = MessagesInConversation.objects.filter(conversation=instance).cache()

        if from_date:
            messages_conversations = messages_conversations.filter(created_at__gte=from_date).cache()

        if to_date:
            messages_conversations = messages_conversations.filter(created_at__lte=to_date).cache()

        Message.objects.filter(pk__in=messages_conversations.values_list('message', flat=True)).cache().update(
            seen=True)

        return Response(status=status.HTTP_200_OK)


send_message = SendPrivateMessageAPIView.as_view()
read_message = ReadMessageView.as_view()
read_conversation = ReadingConversationMessages.as_view()

__all__ = [
    'ConversationAPIView',
    'send_message',
    'read_message',
    'read_conversation',
]
