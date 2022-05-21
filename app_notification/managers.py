from django.contrib.contenttypes.models import ContentType
from django.db import models, transaction


class NotificationManager(models.Manager):

    @transaction.atomic
    def notify(self, sender, receiver, model, group, _type):
        content_type = ContentType.objects.get_for_model(model)

        action, is_new = self.get_or_create(performed_by=sender, performed_on=receiver, group=group, type=_type,
                                            content_type=content_type, object_id=model.pk)

        if not is_new:
            action.delete()

        return action, is_new

    def get_notifications(self, user, from_date, group):
        qs = self.filter(performed_on=user, group=group)

        if from_date:
            qs = qs.filter(created_at__gte=from_date)

        return qs.cache()

    def get_notification_count(self, user, from_date, group):
        return self.get_notifications(user, from_date, group).filter(read_at=None).cache().count()
