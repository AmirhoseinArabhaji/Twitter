from django.contrib.auth import get_user_model
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.viewsets import ModelViewSet

from app_twitter.models import Tweet, Hashtag
from app_twitter.serializers import tweet
from utilities.pagination import PageNumberPagination
from rest_framework.permissions import IsAdminUser

User = get_user_model()


class AdminTwitterManagementViewSet(ModelViewSet):
    queryset = Tweet.objects.all().cache()
    serializer_class = tweet.TweetSerializer
    permission_classes = (IsAdminUser,)
    pagination_class = PageNumberPagination

    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]

    filterset_fields = ['reply_to',  # noqa
                        'retweet',
                        'author'
                        ]

    search_fields = ['@body']

    ordering_fields = [
        'likes_count',
        'views_count',
        'mentions_count',
        'retweets_count',
        'created_at',
        'author',
    ]
    ordering = ['-created_at']


class AdminHashtagManagementViewSet(ModelViewSet):
    queryset = Hashtag.objects.all().cache()
    serializer_class = tweet.AdminHashtagSerializer
    permission_classes = (IsAdminUser,)
    pagination_class = PageNumberPagination

    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]

    search_fields = ['@name']
    ordering_fields = '__all__'
    ordering = ['-updated_at']


__all__ = [
    'AdminTwitterManagementViewSet',
    'AdminHashtagManagementViewSet',
]
