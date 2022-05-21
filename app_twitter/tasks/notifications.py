import pickle

from celery import shared_task
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.db import transaction

from app_notification.models import Notification
from app_twitter.models import Mention, MutedUsers
from utilities.decorators import pickle_input
from utilities.text import mention_extractor

User = get_user_model()


def removing_mentions(object_id):
    with transaction.atomic():
        content_type = ContentType.objects.get(app_label='app_twitter', model='mention')

        Notification.objects.filter(content_type=content_type,
                                    object_id__in=object_id).delete()


def saving_mentions(instance, owner: User):
    if type(instance.body) is str:

        with transaction.atomic():
            mentions = mention_extractor(instance.body)
            users = User.objects.filter(username__in=mentions)

            content_type = ContentType.objects.get(model='mention')

            for user in users:
                Mention.objects.create(mention_by=owner, mention_to=user)
                Notification.objects.create(
                    performed_by=owner,
                    performed_on=user,
                    group=Notification.NotificationsGroups.TWITTER,
                    content_type=content_type,
                    object_id=instance.pk
                )


@pickle_input
@shared_task(bind=True, name='notify', autoretry_for=(Exception,),
             retry_backoff=True,
             retry_jitter=True,
             retry_kwargs={'max_retries': 5})
def notify(self, instance, to: User, by: User, _type, parent_id=None):
    """
    create a new notification
    :param self:
    :param instance:
    :param to:
    :param by:
    :param _type:
    :param parent_id:
    :return:
    """
    instance = pickle.loads(instance)
    to = pickle.loads(to)
    by = pickle.loads(by)
    _type = pickle.loads(_type)

    if not (to == by and not MutedUsers.objects.filter(muter=to, muted=by).cache().exists()):
        content_type = ContentType.objects.get_for_model(instance)

        Notification.objects.create(
            performed_on=to,
            performed_by=by,
            type=_type,
            group=Notification.NotificationsGroups.TWITTER,
            content_type=content_type,
            object_id=instance.pk
        )


__all__ = [
    'notify',
    'saving_mentions',
    'removing_mentions',
]
