from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _

from app_bookmark.managers import BookmarkManager
from app_twitter.models import Tweet

User = get_user_model()


class Bookmark(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookmarks')

    tweet = models.ForeignKey(Tweet, on_delete=models.CASCADE)

    created_at = models.DateTimeField(auto_now_add=True)

    objects = BookmarkManager()

    class Meta:
        ordering = ('-created_at',)

        verbose_name = _('bookmark')
        verbose_name_plural = _('bookmarks')

        constraints = [
            models.UniqueConstraint(fields=('user', 'tweet'),
                                    name='bookmark_unique_constraint')
        ]

        indexes = [
            models.Index(fields=('-created_at',)),
            models.Index(fields=('user', 'tweet')),

        ]

    def __str__(self):
        return f'{self.user} bookmarked {self.tweet}'
