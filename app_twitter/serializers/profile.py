from django.contrib.auth import get_user_model
from django.utils.translation import gettext as _
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from app_like.models import Like
from app_twitter.models import Tweet, Fellowship, MutedUsers
from utilities.serializers import HybridImageField

User = get_user_model()


class TwitterProfileSerializer(serializers.ModelSerializer):
    joined_at = serializers.DateTimeField(source='date_joined', read_only=True)

    follows_you = serializers.SerializerMethodField(read_only=True)
    you_follows = serializers.SerializerMethodField(read_only=True)
    is_muted = serializers.SerializerMethodField(read_only=True)

    avatar = HybridImageField(allow_empty_file=False, allow_null=False, use_url=True, required=False)
    header = HybridImageField(allow_empty_file=False, allow_null=False, use_url=True, required=False)

    username = serializers.CharField(max_length=26, required=False)
    fullname = serializers.CharField(max_length=128, required=False)

    is_private = serializers.BooleanField(default=False, required=False)
    is_active = serializers.BooleanField(read_only=True)

    class Meta:
        model = User
        fields = (
            'is_private',
            'is_active',
            'username',
            'bio',
            'avatar',
            'header',
            'fullname',
            'joined_at',
            'follows_you',
            'you_follows',
            'is_muted',
        )

    def validate(self, attrs):
        username = attrs.pop('username', None)
        user = self.context['request'].user

        if not user.username:
            if username and type(username) is str:
                if User.objects.filter(username__iexact=username).exists():
                    raise ValidationError({"message": _("username does exist!")})
                attrs['username'] = username

        return super().validate(attrs)

    def get_follows_you(self, instance: User):
        user = self.context['request'].user
        if user.is_authenticated:
            return Fellowship.objects.filter(follower=instance, following=user).cache().exists()
        else:
            return False

    def get_you_follows(self, instance: User):
        user = self.context['request'].user
        if user.is_authenticated:
            return Fellowship.objects.filter(follower=user, following=instance).cache().exists()
        else:
            return False

    def get_is_muted(self, instance: User):
        user = self.context['request'].user
        if user.is_authenticated:
            return MutedUsers.objects.filter(muter=user, muted=instance).cache().exists()
        else:
            return False


class AuthorSerializer(TwitterProfileSerializer):
    class Meta(TwitterProfileSerializer.Meta):
        fields = (
            'username',
            'fullname',
            'avatar',
        )

        read_only_fields = fields


class TweetAuthorSerializer(TwitterProfileSerializer):
    class Meta(TwitterProfileSerializer.Meta):
        fields = (
            'username',
            'fullname',
            'you_follows',
            'avatar',
        )

        read_only_fields = fields


class UserSerializer(TwitterProfileSerializer):
    class Meta(TwitterProfileSerializer.Meta):
        fields = (
            'phone',
            'username',
            'fullname',
            'avatar',
        )

        read_only_fields = fields


class ProfileStaticsSerializers(serializers.Serializer):
    tweets_count = serializers.SerializerMethodField(read_only=True)
    likes_count = serializers.SerializerMethodField(read_only=True)
    retweets_count = serializers.SerializerMethodField(read_only=True)
    mentions_count = serializers.SerializerMethodField(read_only=True)
    followers_count = serializers.SerializerMethodField(read_only=True)
    followings_count = serializers.SerializerMethodField(read_only=True)

    class Meta:
        fields = (
            'tweets_count',
            'likes_count',
            'retweets_count',
            'mentions_count',
            'followers_count',
            'followings_count',
        )

    @staticmethod
    def get_tweets_count(user_obj):
        return Tweet.objects.filter(author=user_obj).cache().count()

    @staticmethod
    def get_likes_count(user_obj):
        return Like.objects.filter(user=user_obj).cache().count()

    @staticmethod
    def get_retweets_count(user_obj):
        return Tweet.objects.filter(author=user_obj, retweet__isnull=False).cache().count()

    @staticmethod
    def get_mentions_count(user_obj):
        return Tweet.objects.filter(author=user_obj, reply_to__isnull=False).cache().count()

    @staticmethod
    def get_followers_count(user_obj):
        return Fellowship.objects.filter(following=user_obj).cache().count()

    @staticmethod
    def get_followings_count(user_obj):
        return Fellowship.objects.filter(follower=user_obj).cache().count()

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class MinimalProfileSerializer(TwitterProfileSerializer):
    bio = serializers.SerializerMethodField(read_only=True)

    class Meta(TwitterProfileSerializer.Meta):
        fields = (
            'username',
            'fullname',
            'bio',
            'avatar',
            'is_private',
            'you_follows',
            'follows_you',
        )

    @staticmethod
    def get_bio(user):
        if user.bio:
            bio = user.bio[:20]
            if not bio == user.bio:
                bio += ' ...'
            return bio

        else:
            return None


class TwitterUsernameSearchResult(MinimalProfileSerializer):
    class Meta(MinimalProfileSerializer.Meta):
        fields = (
            'username',
            'fullname',
            'avatar',
        )


class ProfileNotificationInfoSerializer(TwitterProfileSerializer):
    class Meta(TwitterProfileSerializer.Meta):
        fields = (
            'username',
            'fullname',
            'avatar',
        )


__all__ = [
    'TwitterProfileSerializer',
    'AuthorSerializer',
    'ProfileStaticsSerializers',
    'MinimalProfileSerializer',
    'ProfileNotificationInfoSerializer',
    'UserSerializer',
    'TweetAuthorSerializer',
    'TwitterUsernameSearchResult',
]
