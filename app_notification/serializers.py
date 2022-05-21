from rest_framework import serializers

from app_notification.models import Notification


class ReadingNotificationSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(required=True)

    class Meta:
        model = Notification
        fields = (
            'id',
        )


class SendNotificationSerializer(serializers.Serializer):
    users = serializers.ListField(min_length=1, required=True, child=serializers.IntegerField(min_value=1))

    class Meta:
        fields = (
            'users',
        )

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass
