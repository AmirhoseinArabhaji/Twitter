from django.db import transaction
from django.db.models import F

from app_twitter.models import Hashtag, HashtagsUsedInTweets
from utilities.text import hashtag_extractor


def saving_hashtags(instance):
    all_hashtag_used = list()

    if type(instance.body) is str:
        hashtags_set = hashtag_extractor(instance.body)

        with transaction.atomic():
            for hashtag_name in hashtags_set:
                complete_name = f'#{hashtag_name}'
                hashtag, _ = Hashtag.objects.select_for_update().get_or_create(name=complete_name)
                hashtag.usage_count = F('usage_count') + 1
                hashtag.save()
                all_hashtag_used.append(HashtagsUsedInTweets(tweet=instance, hashtag=hashtag))

            if all_hashtag_used:
                HashtagsUsedInTweets.objects.bulk_create(all_hashtag_used, batch_size=min(len(all_hashtag_used), 250))


__all__ = [
    'saving_hashtags',
]
