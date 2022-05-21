import uuid

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.indexes import HashIndex
from django.db import models
from django.utils.translation import gettext_lazy as _

from app_notification.managers import NotificationManager

User = get_user_model()


class Notification(models.Model):
    class NotificationsGroups(models.TextChoices):
        TWITTER = ('twitter', _('twitter'))

    class NotificationsTypes(models.TextChoices):
        LIKE = ('like', _('like'))
        RETWEET = ('retweet', _('retweet'))
        MENTION = ('mention', _('mention'))
        MESSAGE = ('message', _('message'))
        EVENT = ('EVENT', _('event'))

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    performed_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='action_performed', null=True)
    performed_on = models.ForeignKey(User, on_delete=models.CASCADE, related_name='action_received')

    type = models.CharField(max_length=8, choices=NotificationsTypes.choices, default=NotificationsTypes.MENTION)
    group = models.CharField(max_length=32, choices=NotificationsGroups.choices, default=NotificationsGroups.TWITTER)

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, related_name="content_type_actions")
    object_id = models.TextField(null=False)
    content_object = GenericForeignKey('content_type', 'object_id')

    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(default=None, null=True)

    objects = NotificationManager()

    class Meta:
        ordering = ('-created_at',)

        indexes = [
            models.Index(fields=('-created_at',)),
            models.Index(fields=('content_type', 'object_id', 'type', 'group')),
        ]

    def __str__(self):
        return f'{self.type}: {self.performed_by} -> {self.performed_on} at {self.created_at}'
