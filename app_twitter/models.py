import uuid

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericRelation, GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.indexes import HashIndex
from django.db import models
from django.db.models import F
from django.utils.translation import gettext as _

from app_twitter.managers import TweetManager

User = get_user_model()


class Hashtag(models.Model):
    name = models.CharField(primary_key=True, max_length=255, null=False, blank=False)
    usage_count = models.PositiveBigIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)


    class Meta:
        ordering = ('-usage_count',)

        indexes = [
            models.Index(fields=('-usage_count',)),
            HashIndex(fields=('name',), name='hashtag_name_hash_index')
        ]

    def __str__(self):
        return self.name


class Mention(models.Model):
    mention_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='mention_by_user')
    mention_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='mention_to_user')

    def __str__(self):
        return f'{self.mention_by} mentioned {self.mention_to}'


class Fellowship(models.Model):
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followers')
    following = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followed')

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('created_at',)

        indexes = [
            models.Index(fields=('follower', 'following')),
            models.Index(fields=('-created_at',), name='fellowship_created_index')
        ]

        constraints = [
            models.UniqueConstraint(fields=('follower', 'following'), name='fellowship_unique')
        ]

    def __str__(self):
        return f'{self.follower} followed {self.following} at {self.created_at}'


class Tweet(models.Model):
    reply_to = models.ForeignKey('self', null=True, blank=False, related_name='replies', on_delete=models.CASCADE)
    retweet = models.ForeignKey('self', null=True, blank=False, related_name='retweets', on_delete=models.CASCADE)

    author = models.ForeignKey(User, on_delete=models.CASCADE)

    body = models.CharField(max_length=5000, null=True)
    images = models.JSONField(null=True)

    hashtags = models.ManyToManyField(Hashtag, through='HashtagsUsedInTweets')
    mentions = models.ManyToManyField(Mention, through='MentionUsedInTweets')

    created_at = models.DateTimeField(auto_now_add=True)

    vote = models.ForeignKey('app_vote.Vote', null=True, on_delete=models.SET_NULL)

    bookmarks = GenericRelation('app_bookmark.Bookmark', related_query_name='tweet')
    likes = GenericRelation('app_like.Like', related_query_name='tweet')

    likes_count = models.PositiveIntegerField(default=0)
    views_count = models.PositiveBigIntegerField(default=0)
    mentions_count = models.PositiveIntegerField(default=0)
    retweets_count = models.PositiveIntegerField(default=0)

    related_item_content_type = models.ForeignKey(ContentType, on_delete=models.SET_NULL, null=True,
                                                  related_name="content_type_tweets")
    related_item_object_id = models.PositiveIntegerField(null=True)
    related_item_content_object = GenericForeignKey('related_item_content_type', 'related_item_object_id')

    objects = TweetManager()

    class Meta:
        ordering = ('-created_at',)
        indexes = [
            models.Index(fields=('-created_at',), name='tweet_created_at_tree_index'),
            models.Index(fields=('related_item_content_type', 'related_item_object_id'),
                         name='related_item_tree_index'),
            HashIndex(fields=('author',), name='tweet_author_hash_index'),
            HashIndex(fields=('retweet',), name='tweet_retweet_hash_index'),
            HashIndex(fields=('reply_to',), name='tweet_reply_to_hash_index'),
        ]

    def delete(self, using=None, keep_parents=False):
        self.hashtags.update(usage_count=F('usage_count') - 1)

        return super().delete()

    def __str__(self):
        return f'{self.author} tweeted at {self.created_at}'


class HashtagsUsedInTweets(models.Model):
    hashtag = models.ForeignKey(Hashtag, on_delete=models.SET_NULL, null=True)
    tweet = models.ForeignKey(Tweet, on_delete=models.CASCADE, null=True)


class MentionUsedInTweets(models.Model):
    mention = models.ForeignKey(Mention, on_delete=models.SET_NULL, null=True)
    tweet = models.ForeignKey(Tweet, on_delete=models.SET_NULL, null=True)


class Message(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='+')
    contact = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='+')

    body = models.TextField(editable=False)

    seen = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-created_at',)
        indexes = [
            HashIndex(fields=('id',)),
            models.Index(fields=('id', 'contact')),
        ]


class Conversation(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)

    starter_participant = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='+')
    contact_participant = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='+')

    messages = models.ManyToManyField(Message, through='MessagesInConversation')

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-updated_at',)
        indexes = [
            models.Index(fields=('starter_participant', 'contact_participant'), name='conversation_participant_index')
        ]


class MessagesInConversation(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)

    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE)
    message = models.ForeignKey(Message, on_delete=models.SET_NULL, null=True)

    created_at = models.DateTimeField(auto_now_add=True, editable=False)

    class Meta:
        indexes = [
            models.Index(fields=('-created_at', 'message'))
        ]


class BlockList(models.Model):
    class BlockListManager(models.Manager):
        def is_blocked(self, blocker, blocked):
            """
            Check if the user is blocked or not
            :param blocker:
            :param blocked:
            :return:
            """
            if not blocker.is_authenticated:
                return False
            else:
                return self.filter(blocker=blocker, blocked=blocked).cache().exists()

    blocker = models.ForeignKey(User, on_delete=models.CASCADE, related_name='+')
    blocked = models.ForeignKey(User, on_delete=models.CASCADE, related_name='+')

    created_at = models.DateTimeField(auto_now_add=True, editable=False)

    objects = BlockListManager()

    class Meta:
        ordering = ('-created_at',)

        indexes = [
            models.Index(fields=('blocker', 'blocked'))
        ]

        constraints = [
            models.UniqueConstraint(fields=('blocker', 'blocked'), name='block_unique_constraints')
        ]

    def __str__(self):
        return f'{self.blocker} blocked {self.blocked}'


class WaitingForResponse(models.Model):
    class Types(models.TextChoices):
        FOLLOWING = 'following', _('following')
        DM = 'direct message', _('direct message')

    type = models.CharField(max_length=16, choices=Types.choices, default=Types.FOLLOWING)

    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='+')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='+')

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-created_at',)

        indexes = [
            models.Index(fields=('from_user', 'to_user', 'type'), )
        ]

        constraints = [
            models.UniqueConstraint(fields=('from_user', 'to_user', 'type'), name='from_to_type_waiting_constraint')
        ]


class MutedUsers(models.Model):
    muter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='+')
    muted = models.ForeignKey(User, on_delete=models.CASCADE, related_name='+')

    class Meta:
        ordering = ('id',)

        indexes = [
            models.Index(fields=('muter', 'muted'))
        ]
