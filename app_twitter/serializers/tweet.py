from bs4 import BeautifulSoup
from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers

from app_bookmark.models import Bookmark
from app_like.models import Like
from app_twitter.models import Tweet, MentionUsedInTweets, Hashtag, MutedUsers
from app_twitter.serializers.profile import AuthorSerializer, TweetAuthorSerializer
from app_twitter.tasks.notifications import removing_mentions, saving_mentions
from app_twitter.tasks.pre_process import saving_hashtags
from app_upload.validators import twitter_image_url_validator
from app_vote.serializers import VoteSerializer


class HashtagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hashtag
        fields = ('name',)


class AdminHashtagSerializer(HashtagSerializer):
    class Meta(HashtagSerializer.Meta):
        fields = '__all__'


class RetweetedTweetSerializer(serializers.ModelSerializer):
    body = serializers.SerializerMethodField(read_only=True)
    author = AuthorSerializer(read_only=True)

    class Meta:
        model = Tweet
        fields = (
            'id',
            'author',
            'body',
            'created_at',
        )

        read_only_fields = fields

    @staticmethod
    def get_body(instance):
        if type(instance.body) is str:
            summarized_body = instance.body[:100]

            if len(summarized_body) != len(instance.body):
                summarized_body += '...'

            return summarized_body
        else:
            return None


class TweetSerializer(serializers.ModelSerializer):
    author = TweetAuthorSerializer(read_only=True)
    body = serializers.CharField(required=True, max_length=5000, allow_null=False, allow_blank=False)
    retweet = serializers.SerializerMethodField(read_only=True)

    is_liked = serializers.SerializerMethodField(read_only=True)
    retweeted = serializers.SerializerMethodField(read_only=True)
    is_bookmarked = serializers.SerializerMethodField(read_only=True)
    is_muted = serializers.SerializerMethodField(read_only=True)

    images = serializers.ListField(max_length=10, allow_empty=True, required=False,
                                   child=serializers.URLField(allow_blank=False, allow_null=False),
                                   validators=[twitter_image_url_validator],
                                   )

    vote = VoteSerializer(many=False, required=False)

    related_item_content_type = serializers.CharField(required=False, allow_null=True, write_only=True)
    related_item_pk = serializers.CharField(required=False, allow_null=True, write_only=True)

    class Meta:
        model = Tweet
        fields = (
            'id',
            'author',
            'body',
            'vote',
            'images',
            'retweet',
            'created_at',
            'likes_count',
            'retweets_count',
            'mentions_count',
            'is_liked',
            'retweeted',
            'is_bookmarked',
            'is_muted',
            'related_item_content_type',
            'related_item_pk',
        )

        read_only_fields = (
            'author',
            'retweet',
            'created_at',
            'likes_count',
            'retweets_count',
            'mentions_count',
            'is_muted',
        )

    def get_is_muted(self, instance: Tweet):
        request = self.context.get('request', None)
        if request and request.user.is_authenticated:
            return MutedUsers.objects.filter(muter=request.user, muted=instance.author).cache().exists()
        else:
            return False

    def get_is_liked(self, instance: Tweet):
        request = self.context.get('request', None)
        if request:
            return Like.objects.is_liked(user=request.user, instance=instance)
        else:
            return False

    def get_retweeted(self, instance: Tweet):
        request = self.context.get('request', None)
        if request and request.user.is_authenticated:
            return Tweet.objects.filter(author=request.user, retweet=instance).cache().exists()
        else:
            return False

    def get_is_bookmarked(self, instance: Tweet):
        request = self.context.get('request', None)
        if request:
            return Bookmark.objects.is_bookmarked(user=request.user, instance=instance)
        else:
            return False

    @staticmethod
    def get_retweet(instance: Tweet):
        if instance.retweet:
            return RetweetedTweetSerializer(instance.retweet).data
        else:
            return None

    def validate(self, attrs):
        body = attrs.get('body', None)

        if body:
            body = BeautifulSoup(body, "lxml").text
            attrs['body'] = body

        return super().validate(attrs)

    def create(self, validated_data):

        validated_data['reply_to'] = self.context.get('reply_to')
        validated_data['retweet'] = self.context.get('retweet')

        related_item_content_type = validated_data.pop('related_item_content_type', None)
        related_item_pk = validated_data.pop('related_item_pk', None)

        vote = validated_data.pop('vote', None)
        vote_instance = None

        if vote:
            serializer = VoteSerializer(data=vote, many=False, context=self.context)
            serializer.is_valid(raise_exception=True)

            vote_instance = serializer.create(serializer.validated_data)

        tweet_instance = Tweet.objects.create(author=self.context['request'].user, vote=vote_instance, **validated_data)

        saving_hashtags(tweet_instance)
        saving_mentions(tweet_instance, self.context['request'].user)

        if related_item_pk and related_item_content_type:
            parts = related_item_content_type.split('_')

            model_name = parts.pop()
            app_label = '_'.join(parts)

            if content_type := ContentType.objects.filter(app_label=app_label, model=model_name).cache(
                    timeout=60 * 60 * 24 * 365).first():

                item_class = content_type.model_class()

                if item_class.objects.filter(pk=related_item_pk).first():
                    tweet_instance.related_item_content_type = content_type
                    tweet_instance.related_item_object_id = related_item_pk
                    tweet_instance.save(update_fields=['related_item_content_type', 'related_item_object_id'])

        return tweet_instance

    def update(self, instance: Tweet, validated_data):

        validated_data.pop('vote', None)

        older_mentions = MentionUsedInTweets.objects.filter(tweet=instance).values_list('pk', flat=True)
        instance.hashtags.clear()

        removing_mentions(older_mentions)
        saving_mentions(instance, self.context['request'].user)

        instance = super().update(instance, validated_data)

        return instance


class RetweetSerializer(TweetSerializer):
    body = serializers.CharField(required=False, max_length=500, allow_null=True, allow_blank=False)


__all__ = [
    'RetweetSerializer',
    'TweetSerializer',
    'RetweetedTweetSerializer',
    'HashtagSerializer',
]
