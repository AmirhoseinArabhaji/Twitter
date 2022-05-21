from django.db import models


class TweetQuerySet(models.QuerySet):
    def timeline_tweets(self):
        return self.select_related('author').filter(author__is_private=False, reply_to__isnull=True).all()


class TweetManager(models.Manager):
    def get_queryset(self):
        return TweetQuerySet(self.model, using=self._db)

    def timeline_tweets(self):
        return self.get_queryset().timeline_tweets()
