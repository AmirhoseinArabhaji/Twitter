from datetime import datetime

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Count
from django.utils.http import parse_http_date_safe
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404, ListAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from app_like.models import Like
from app_notification.models import Notification
from app_twitter.models import Fellowship, BlockList, Tweet, MutedUsers
from app_twitter.permissions import *
from app_twitter.serializers.notifications import NotificationSerializer
from app_twitter.serializers.profile import *
from app_twitter.serializers.tweet import TweetSerializer

User = get_user_model()


class ProfileViewSet(ModelViewSet):
    serializer_class = TwitterProfileSerializer
    permission_classes = [IsOwnerOrReadOnly]
    lookup_field = 'username'
    queryset = User.objects.all().cache()

    def get_queryset(self):
        if self.action == 'list':
            return User.objects.none()
        else:
            return super().get_queryset()

    def get_permissions(self):
        if self.action == 'retrieve':
            if not self.request.user.is_authenticated:
                return AllowAny(),
            else:
                return [
                    IsPrivate(),
                    IsBlocked(),
                    BlockedYou(),
                ]

        elif self.action == 'list':
            return IsAuthenticated(),
        else:
            return super().get_permissions()

    def list(self, request, *args, **kwargs):
        return Response(status=status.HTTP_200_OK, data=self.get_serializer(request.user).data)

    @transaction.atomic
    @action(methods=['patch'], detail=False, permission_classes=[
        IsAuthenticated,
    ])
    def update_profile(self, request):
        user = request.user

        serializer = self.get_serializer(user, data=request.data, many=False)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(status=status.HTTP_200_OK, data=serializer.data)

    @transaction.atomic
    @action(methods=['put'], detail=True, permission_classes=[
        IsAuthenticated,
        UsernameIsActive,
    ])
    def follow(self, request, username):
        if request.user.username == username:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        following = get_object_or_404(queryset=User.objects.select_for_update(), username=username)

        _, result = Fellowship.objects.get_or_create(follower=request.user, following=following)

        return Response(status=status.HTTP_202_ACCEPTED if result else status.HTTP_204_NO_CONTENT)

    @transaction.atomic
    @action(methods=['put'], detail=True, permission_classes=[
        IsAuthenticated,
        UsernameIsActive,
    ])
    def unfollow(self, request, username):
        if request.user.username == username:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        following = get_object_or_404(queryset=User.objects.select_for_update(), username=username)

        fellowship_instance = get_object_or_404(queryset=Fellowship.objects.select_for_update(), follower=request.user,
                                                following=following)
        fellowship_instance.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['put'], detail=True, permission_classes=[
        IsAuthenticated,
        UsernameIsActive,
    ])
    def block(self, request, username):
        # TODO: after blocking all like and bookmarks must be remove for both sides
        if request.user.username == username:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        to_block = get_object_or_404(queryset=User, username=username)
        instance, blocked = BlockList.objects.get_or_create(blocked=to_block, blocker=request.user)

        if not blocked:
            instance.delete()

        return Response(status=status.HTTP_200_OK, data={'blocked': blocked})

    @action(methods=['put'], detail=True, permission_classes=[
        IsAuthenticated,
        UsernameIsActive,
    ])
    def mute(self, request, username):
        if request.user.username == username:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        to_mute = get_object_or_404(queryset=User, username=username)
        instance, muted = MutedUsers.objects.get_or_create(muted=to_mute, muter=request.user)

        if not muted:
            instance.delete()

        return Response(status=status.HTTP_200_OK, data={'muted': muted})


class FollowersView(ListAPIView):
    queryset = Fellowship.objects.select_related('following').all()
    permission_classes = [
        IsAuthenticated,
        IsPrivate,
        IsBlocked,
        BlockedYou,
    ]
    serializer_class = MinimalProfileSerializer

    lookup_field = 'username'

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Fellowship.objects.none()

        user = get_object_or_404(User, **{self.lookup_field: self.kwargs[self.lookup_field]})

        self.check_object_permissions(self.request, user)

        users = super().get_queryset().filter(following=user).cache().values_list('follower', flat=True)
        return User.objects.filter(pk__in=users).cache()


class FollowingsView(ListAPIView):
    queryset = Fellowship.objects.select_related('follower').all()
    permission_classes = [
        IsAuthenticated,
        IsPrivate,
        IsBlocked,
        BlockedYou,
    ]
    serializer_class = MinimalProfileSerializer

    lookup_field = 'username'

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Fellowship.objects.none()

        user = get_object_or_404(User, **{self.lookup_field: self.kwargs[self.lookup_field]})

        self.check_object_permissions(self.request, user)

        users = super().get_queryset().filter(follower=user).cache().values_list('following', flat=True)
        return User.objects.filter(pk__in=users).cache()


class ProfileStaticsAPIView(RetrieveAPIView):
    queryset = User.objects.all().cache()
    permission_classes = [
        IsPrivate,
        IsBlocked,
        BlockedYou,
    ]
    serializer_class = ProfileStaticsSerializers

    lookup_field = 'username'

    def get_permissions(self):
        if not self.request.user.is_authenticated:
            return AllowAny(),
        else:
            return super().get_permissions()


class ProfileTweets(ListAPIView):
    queryset = Tweet.objects.select_related('author').all()
    permission_classes = [
        IsPrivate,
        IsBlocked,
        BlockedYou,
    ]
    serializer_class = TweetSerializer

    lookup_field = 'username'

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Tweet.objects.none()

        user = get_object_or_404(User, **{self.lookup_field: self.kwargs[self.lookup_field]})
        filter_type = self.request.query_params.get('type', None)

        if filter_type:
            qs = super().get_queryset().filter(author=user)

            if filter_type == 'reply':
                tweets_list = qs.filter(reply_to__isnull=False, author__is_private=False). \
                    values_list('reply_to', flat=True).cache()

                return super().get_queryset().filter(pk__in=tweets_list).cache()

            elif filter_type == 'retweet':
                return qs.filter(retweet__isnull=False).cache()

            elif filter_type == "like":
                liked_tweets = Like.objects.get_liked_object_ids(user=user)
                return super().get_queryset().filter(pk__in=liked_tweets).cache()

        else:
            return super().get_queryset().filter(author=user, reply_to__isnull=True).cache()


class ProfileNotifications(ListAPIView):
    queryset = Notification.objects.none()
    serializer_class = NotificationSerializer
    permission_classes = [
        IsAuthenticated,
    ]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Notification.objects.none()

        if_modified_since = self.request.META.get('HTTP_IF_MODIFIED_SINCE')
        if_modified_since = if_modified_since and parse_http_date_safe(if_modified_since)

        _datetime = None

        if if_modified_since:
            _datetime = datetime.fromtimestamp(if_modified_since)

        return Notification.objects.get_notifications(user=self.request.user,
                                                      from_date=_datetime,
                                                      group=Notification.NotificationsGroups.TWITTER)


class ProfileNotificationsCount(ListAPIView):
    queryset = Notification.objects.none()
    serializer_class = NotificationSerializer
    permission_classes = [
        IsAuthenticated,
    ]

    def list(self, request, *args, **kwargs):
        if_modified_since = self.request.META.get('HTTP_IF_MODIFIED_SINCE')
        if_modified_since = if_modified_since and parse_http_date_safe(if_modified_since)

        _datetime = None

        if if_modified_since:
            _datetime = datetime.fromtimestamp(if_modified_since)

        count = Notification.objects.get_notification_count(user=self.request.user,
                                                            from_date=_datetime,
                                                            group=Notification.NotificationsGroups.TWITTER)

        return Response(status=status.HTTP_200_OK, data={'count': count})


class ProfileBlockedList(ListAPIView):
    queryset = BlockList.objects.all()
    serializer_class = AuthorSerializer
    permission_classes = [
        IsAuthenticated,
    ]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return BlockList.objects.none()

        users = super().get_queryset().filter(blocker=self.request.user).values_list('blocked', flat=True)
        return User.objects.filter(pk__in=users)


class ProfileLikedList(ListAPIView):
    queryset = Like.objects.none()
    serializer_class = AuthorSerializer
    permission_classes = [
        IsAuthenticated,
    ]

    def get_queryset(self):
        return Tweet.objects.select_related('author').filter(
            pk__in=Like.objects.get_liked_object_ids(user=self.request.user), author__is_private=False).cache()


class MostFollowedProfiles(ListAPIView):
    queryset = Fellowship.objects.values('following').annotate(count=Count('follower')). \
                   order_by('-count')[:10].values_list('following', flat=True)
    serializer_class = MinimalProfileSerializer
    permission_classes = [
        AllowAny,
    ]

    def get_queryset(self):
        return User.objects.filter(pk__in=super().get_queryset()).order_by().cache()


statics = ProfileStaticsAPIView.as_view()
followers = FollowersView.as_view()
followings = FollowingsView.as_view()
profile_tweets = ProfileTweets.as_view()
profile_blocked = ProfileBlockedList.as_view()
notifications = ProfileNotifications.as_view()
notifications_count = ProfileNotificationsCount.as_view()
trend_profiles = MostFollowedProfiles.as_view()

__all__ = [
    'profile_tweets',
    'statics',
    'followers',
    'followings',
    'ProfileViewSet',
    'notifications',
    'notifications_count',
    'profile_blocked',
    'trend_profiles',
]
