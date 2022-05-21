from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _

from app_like.managers import LikeManager
from app_twitter.models import Tweet

User = get_user_model()


class Like(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='likes')

    is_dislike = models.BooleanField(default=False, editable=False)

    tweet = models.ForeignKey(Tweet, on_delete=models.CASCADE)

    created_at = models.DateTimeField(auto_now_add=True)

    objects = LikeManager()

    class Meta:
        ordering = ('-created_at',)

        verbose_name = _('like')
        verbose_name_plural = _('likes')

        constraints = [
            models.UniqueConstraint(fields=('user', 'tweet', 'is_dislike'),
                                    name='like_unique_constraint')
        ]

        indexes = [
            models.Index(fields=('-created_at',)),
            models.Index(fields=('user', 'tweet', 'is_dislike')),
        ]

    def __str__(self):
        return f'{self.user} liked {self.tweet}'
