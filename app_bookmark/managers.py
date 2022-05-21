from typing import Tuple

from django.db import models, transaction
from django.utils.translation import gettext as _


class BookmarkManager(models.Manager):

    @transaction.atomic
    def is_bookmarked(self, user, instance) -> bool:
        """
        Check if the object is bookmarked or not.
        :param user:
        :param instance:
        :return bool:
        """

        if not user.is_authenticated:
            return False

        return self.filter(user=user, tweet=instance).cache().exists()

    @transaction.atomic
    def bookmark(self, user, instance) -> Tuple[object, str]:
        """
        Check if the object was bookmarked or not, if not, it will be add to the bookmarks
        else it will be remove from the bookmarks table.
        it returns the proper message based on the situation.
        :param user:
        :param instance:
        :return Tuple[object, str]:
        """
        bookmark, bookmarked = self.get_or_create(user=user, tweet_id=instance.id)

        if not bookmarked:
            bookmark.delete()

        return bookmarked, _(f"{instance} {'removed from' if not bookmarked else 'added to'}"
                             f" your bookmarks list.")

    def get_bookmarked_object_ids(self, user, **kwargs) -> list:
        """
        It returns list of bookmarked object ids, the result
        is sorted based on the creation date.
        :param user:
        :param kwargs:
        :return list:
        """
        return self.filter(user=user, **kwargs).values_list('tweet', flat=True)
