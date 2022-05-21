from typing import Tuple

from django.db import models, transaction
from django.utils.translation import gettext as _


class LikeManager(models.Manager):

    def is_liked(self, user, instance, no_cache=False) -> bool:
        """
        Check if the object is liked or not.
        :param user:
        :param instance:
        :param no_cache: whether to cache the query using CacheOps or not.
        :return bool:
        """

        if not user.is_authenticated:
            return False

        qs = self.filter(user=user, is_dislike=False, tweet=instance)

        if no_cache:
            return qs.exists()

        return qs.cache().exists()

    def is_disliked(self, user, instance, no_cache=False) -> bool:
        """
        Check if the object is disliked or not.
        :param user:
        :param instance:
        :param no_cache: whether to cache the query using CacheOps or not.
        :return bool:
        """

        if not user.is_authenticated:
            return False

        qs = self.filter(user=user, is_dislike=True, tweet=instance)

        if no_cache:
            return qs.exists()

        return qs.cache().exists()

    @transaction.atomic
    def like(self, user, instance) -> Tuple[object, str]:
        """
        Check if the object was liked or not, if not, it will be add to the likes
        else it will be remove from the likes table. Also if the object was previously
        disliked, it will remove if from dislikes table.
        it returns the proper message based on the situation.
        :param user:
        :param instance:
        :return Tuple[object, str]:
        """

        previously_disliked = self.filter(user=user, is_dislike=True, tweet=instance).first()
        if previously_disliked:
            previously_disliked.delete()
            if hasattr(instance, 'dislikes_count'):
                instance.dislikes_count -= 1
                instance.save(update_fields=['dislikes_count'])

        like, liked = self.get_or_create(user=user, is_dislike=False, tweet_id=instance.id)

        if not liked:
            like.delete()
            if hasattr(instance, 'likes_count'):
                instance.likes_count -= 1
                instance.save(update_fields=['likes_count'])

        else:
            if hasattr(instance, 'likes_count'):
                instance.likes_count += 1
                instance.save(update_fields=['likes_count'])

        return liked, _(f"{instance} {'removed from' if not liked else 'added to'}"
                        f" your likes list.")

    @transaction.atomic
    def dislike(self, user, instance) -> Tuple[object, str]:
        """
        Check if the object was disliked or not, if not, it will be add to the likes
        else it will be remove from the dislikes table. Also if the object was previously
        liked, it will remove if from likes table.
        it returns the proper message based on the situation.
        :param user:
        :param instance:
        :return Tuple[object, str]:
        """

        previously_liked = self.filter(user=user, is_dislike=False, tweet=instance).first()
        if previously_liked:
            previously_liked.delete()
            if hasattr(instance, 'likes_count'):
                instance.likes_count -= 1
                instance.save(update_fields=['likes_count'])

        like, disliked = self.get_or_create(user=user, is_dislike=True, tweet_id=instance.id)

        if not disliked:
            like.delete()
            if hasattr(instance, 'dislikes_count'):
                instance.dislikes_count -= 1
                instance.save(update_fields=['dislikes_count'])

        else:
            if hasattr(instance, 'likes_count'):
                instance.dislikes_count += 1
                instance.save(update_fields=['dislikes_count'])

        return disliked, _(f"{instance} {'removed from' if not disliked else 'added to'}"
                           f" your dislikes list.")

    def get_liked_object_ids(self, user, **kwargs) -> list:
        """
        It returns list of liked object ids, the result
        is sorted based on the creation date.
        :param user:
        :param kwargs:
        :return list:
        """
        return self.filter(user=user, is_dislike=False, **kwargs).values_list('object_id', flat=True)

    def get_disliked_object_ids(self, user, **kwargs) -> list:
        """
        It returns list of disliked object ids, the result
        is sorted based on the creation date.
        :param user:
        :param kwargs:
        :return list:
        """
        return self.filter(user=user, is_dislike=True, **kwargs).values_list('object_id', flat=True)

    def who_liked_it(self, instance):
        """
        Returns the users pk list whom liked the instance
        :param instance:
        :return:
        """
        return self.model.objects.select_related('user').filter(is_dislike=False,
                                                                tweet=instance).values_list('user', flat=True)

    def who_disliked_it(self, instance):
        """
        Returns the users pk list whom disliked the instance
        :param instance:
        :return:
        """
        return self.model.objects.select_related('user').filter(is_dislike=True,
                                                                tweet=instance).values_list('user', flat=True)
