from rest_framework import serializers

from app_notification.models import Notification
from app_twitter.models import Tweet, Conversation
from app_twitter.serializers.profile import ProfileNotificationInfoSerializer
from app_twitter.serializers.message import ConversationSerializer
from app_twitter.serializers.tweet import TweetSerializer


class TweetNotificationSerializer(TweetSerializer):
    class Meta(TweetSerializer.Meta):
        model = Tweet
        fields = (
            'id',
            'reply_to',
            'body',
            'created_at',
        )


class NotificationSerializer(serializers.ModelSerializer):
    notify_by = ProfileNotificationInfoSerializer(read_only=True, source='performed_by')
    notification_group = serializers.CharField(read_only=True, source='group')
    notification_type = serializers.CharField(read_only=True, source='type')

    content = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Notification
        fields = (
            'id',
            'notify_by',
            'notification_group',
            'notification_type',
            'content',
            'created_at',
            'read_at',
        )

        read_only_fields = fields

    def get_content(self, instance: Notification):
        if not instance.type == Notification.NotificationsTypes.MESSAGE:
            try:
                instance = Tweet.objects.get(pk=instance.object_id)
                return TweetNotificationSerializer(instance=instance, context=self.context).data

            except Tweet.DoesNotExist:
                return None
        else:
            try:
                instance = Conversation.objects.get(pk=instance.object_id)
                return ConversationSerializer(instance=instance, context=self.context).data

            except Conversation.DoesNotExist:
                return None
