from datetime import datetime

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Q
from django.http import Http404
from django.utils.http import parse_http_date_safe
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404, RetrieveAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from app_bookmark.models import Bookmark
from app_like.models import Like
from app_notification.models import Notification
from app_twitter.models import Tweet, Fellowship, BlockList, Hashtag, MutedUsers
from app_twitter.permissions import *
from app_twitter.serializers.hashtag import HashTagSerializer
from app_twitter.serializers.profile import MinimalProfileSerializer
from app_twitter.serializers.tweet import *
from app_twitter.tasks.notifications import notify

User = get_user_model()


class TweetViewSet(ModelViewSet):
    queryset = Tweet.objects.timeline_tweets()
    serializer_class = TweetSerializer
    permission_classes = [IsOwnerOrReadOnly, IsAuthenticated]

    def get_queryset(self):
        # TODO : this method should be clear

        if self.action == 'retrieve':
            return Tweet.objects.select_related('author').all()

        qs = super().get_queryset()

        if self.request.user.is_authenticated:
            blocked_profiles = BlockList.objects.filter(blocker=self.request.user).cache().values_list('blocked',
                                                                                                       flat=True)
            blocked_user = BlockList.objects.filter(blocked=self.request.user).cache().values_list('blocker',
                                                                                                   flat=True)

            muted_users = MutedUsers.objects.filter(muter=self.request.user).cache().values_list('muted',
                                                                                                 flat=True)
            qs = qs.filter(~Q(author__in=list(set(blocked_profiles) | set(blocked_user) | set(muted_users))))

        before = self.request.query_params.get('before', None)
        before = before and parse_http_date_safe(before)
        if before:
            dt = datetime.fromtimestamp(before)
            qs = qs.filter(created_at__lte=dt)

        if_modified_since = self.request.META.get('HTTP_IF_MODIFIED_SINCE')
        if_modified_since = if_modified_since and parse_http_date_safe(if_modified_since)

        if if_modified_since:
            dt = datetime.fromtimestamp(if_modified_since)
            qs = qs.filter(created_at__gte=dt)

        filter_by = self.request.query_params.get('filter', None)

        if filter_by == 'following' or filter_by == 'hashtag':
            search_term = self.request.query_params.get('q', None)

            if search_term:
                return qs.filter(hashtags__name__contains=search_term).cache()

        if self.request.user.is_authenticated and type(filter_by) is str and filter_by.lower() == 'following':
            followings = Fellowship.objects.filter(follower=self.request.user).cache() \
                .values_list('following', flat=True)

            return qs.filter(Q(author__in=followings) | Q(author=self.request.user)).cache()

        return qs.cache()

    def get_permissions(self):
        if self.action == 'create':
            return [
                IsAuthenticated(),
                UsernameIsActive(),
            ]
        elif self.action in ['bookmark', 'report']:
            return [
                IsAuthenticated(),
                IsPrivate(),
                IsBlocked(),
                BlockedYou(),
            ]
        elif self.action in ['reply', 'retweet', 'like']:
            return [
                IsAuthenticated(),
                UsernameIsActive(),
                IsPrivate(),
                IsBlocked(),
                BlockedYou(),
            ]
        else:
            return super().get_permissions()

    def check_object_permissions(self, request, obj):
        return super().check_object_permissions(request, obj.author)

    @transaction.atomic
    @action(methods=['post'], detail=True, permission_classes=[
        IsAuthenticated,
        UsernameIsActive,
        IsPrivate,
        IsBlocked,
        BlockedYou,
    ])
    def reply(self, request, pk):
        tweet = get_object_or_404(Tweet, pk=pk)

        self.check_object_permissions(request, tweet)

        serializer = TweetSerializer(data=request.data, context={'request': request, 'reply_to': tweet})
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            new_tweet = serializer.create(serializer.validated_data)

            tweet.mentions_count += 1
            tweet.save()

        notify(instance=new_tweet,
               to=tweet.author,
               by=request.user,
               _type=Notification.NotificationsTypes.MENTION,
               parent_id=tweet.pk)

        return Response(status=status.HTTP_202_ACCEPTED,
                        data=TweetSerializer(new_tweet, context={'request': request}).data)

    @action(methods=['post'], detail=True, permission_classes=[
        IsAuthenticated,
        UsernameIsActive,
        IsPrivate,
        IsBlocked,
        BlockedYou,
    ])
    def retweet(self, request, pk):
        tweet = get_object_or_404(Tweet, pk=pk)

        self.check_object_permissions(request, tweet)

        if tweet.retweet and tweet.body is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        serializer = RetweetSerializer(data=request.data, context={'request': request, 'retweet': tweet})
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            new_tweet = serializer.create(serializer.validated_data)

            tweet.retweets_count += 1
            tweet.save()

        notify(instance=tweet if new_tweet.body is None else new_tweet,
               to=tweet.author,
               by=request.user,
               _type=Notification.NotificationsTypes.RETWEET)

        return Response(status=status.HTTP_202_ACCEPTED,
                        data={
                            'created': TweetSerializer(new_tweet, context={'request': request}).data,
                            'retweeted': TweetSerializer(tweet, context={'request': request}).data
                        })

    @action(methods=['post'], detail=True, permission_classes=[
        IsAuthenticated,
        UsernameIsActive,
        IsPrivate,
        IsBlocked,
        BlockedYou,
    ])
    def like(self, request, pk):
        tweet = get_object_or_404(Tweet, pk=pk)

        self.check_object_permissions(request, tweet)

        liked, _ = Like.objects.like(user=request.user, instance=tweet)

        if liked:
            notify(instance=tweet,
                   to=tweet.author,
                   by=request.user,
                   _type=Notification.NotificationsTypes.LIKE)

        return Response(status=status.HTTP_202_ACCEPTED,
                        data=TweetSerializer(tweet, context={'request': request}).data)

    @action(methods=['post'], detail=True, permission_classes=[
        IsAuthenticated,
        IsPrivate,
        IsBlocked,
        BlockedYou,
    ])
    def bookmark(self, request, pk):
        tweet = get_object_or_404(Tweet, pk=pk)

        self.check_object_permissions(request, tweet)

        bookmarked, _ = Bookmark.objects.bookmark(user=request.user, instance=tweet)

        return Response(status=status.HTTP_202_ACCEPTED,
                        data=TweetSerializer(tweet, context={'request': request}).data)


class TweetMentions(RetrieveAPIView):
    queryset = Tweet.objects.all()
    permission_classes = [
        IsPrivate,
        IsBlocked,
        BlockedYou
    ]
    serializer_class = TweetSerializer

    def check_object_permissions(self, request, obj):
        return super().check_object_permissions(request, obj.author)

    def retrieve(self, request, *args, **kwargs):
        tweet = self.get_object()

        return Response(TweetSerializer(self.get_queryset().filter(reply_to=tweet).cache(), many=True,
                                        context={'request': request}).data)


class TweetRetweets(RetrieveAPIView):
    queryset = Tweet.objects.select_related('author').all().cache()
    permission_classes = [
        IsPrivate,
        IsBlocked,
        BlockedYou
    ]
    serializer_class = TweetSerializer

    def check_object_permissions(self, request, obj):
        return super().check_object_permissions(request, obj.author)

    def retrieve(self, request, *args, **kwargs):
        tweet = self.get_object()

        self.check_object_permissions(request, tweet)

        return Response(
            TweetSerializer(self.get_queryset().filter(body__isnull=True, retweet=tweet).cache(), many=True,
                            context={'request': request}).data)


class TweetLikes(RetrieveAPIView):
    queryset = Tweet.objects.all().cache()
    permission_classes = [
        IsPrivate,
        IsBlocked,
        BlockedYou
    ]
    serializer_class = TweetSerializer

    def check_object_permissions(self, request, obj):
        return super().check_object_permissions(request, obj.author)

    def retrieve(self, request, *args, **kwargs):
        tweet = self.get_object()

        self.check_object_permissions(request, tweet)

        users = Like.objects.who_liked_it(tweet)
        return Response(MinimalProfileSerializer(User.objects.filter(pk__in=users).cache(), many=True,
                                                 context={'request': request}).data)


class TweetVote(RetrieveAPIView):
    pass


class TweetQuotes(RetrieveAPIView):
    queryset = Tweet.objects.select_related('author').all().cache()
    permission_classes = [
        IsPrivate,
        IsBlocked,
        BlockedYou
    ]
    serializer_class = TweetSerializer

    def check_object_permissions(self, request, obj):
        return super().check_object_permissions(request, obj.author)

    def retrieve(self, request, *args, **kwargs):
        tweet = self.get_object()

        self.check_object_permissions(request, tweet)

        authors = self.get_queryset().filter(body__isnull=False, retweet=tweet).cache().values_list('author', flat=True)
        return Response(MinimalProfileSerializer(User.objects.filter(pk__in=authors).cache(), many=True,
                                                 context={'request': request}).data)


class HashTagRetrieveView(RetrieveAPIView):
    queryset = Hashtag.objects.all().cache()
    serializer_class = HashTagSerializer
    permission_classes = (AllowAny,)

    lookup_field = 'name'

    def get_object(self):
        name = self.kwargs.get(self.lookup_url_kwarg or self.lookup_field, None)
        if not name:
            raise Http404

        filter_kwargs = {self.lookup_field: name}

        hashtag = self.get_queryset().filter(**filter_kwargs)

        if hashtag.exists():
            return hashtag.first()

        else:
            return Hashtag(name=name)
