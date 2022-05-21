import uuid

from django.contrib.auth import get_user_model
from django.contrib.postgres.indexes import HashIndex
from django.db import models, transaction
from django.db.models import F

User = get_user_model()


class Choice(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=512)
    count = models.PositiveBigIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('created_at',)

        indexes = [
            HashIndex(fields=('title',), )
        ]


class Vote(models.Model):
    class VoteManager(models.Manager):

        @transaction.atomic
        def vote(self, choice_pk):
            Choice.objects.filter(pk=choice_pk).update(count=F('count') + 1)

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)

    expire_date = models.DateTimeField()
    choices = models.ManyToManyField(Choice, through='VoteChoices')

    result = models.JSONField(default=dict)


class VoteChoices(models.Model):
    vote = models.ForeignKey(Vote, on_delete=models.CASCADE)
    choice = models.ForeignKey(Choice, on_delete=models.CASCADE)


class UserVoteHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    vote = models.ForeignKey(Vote, on_delete=models.CASCADE)
    choice = models.ForeignKey(Choice, on_delete=models.CASCADE)

    class Meta:
        indexes = [
            models.Index(fields=('user', 'vote'))
        ]
