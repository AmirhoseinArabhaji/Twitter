from django.urls import path, include
from rest_framework import routers

from app_twitter.views.message import *
from app_twitter.views.profile import *
from app_twitter.views.search import *
from app_twitter.views.trends import hashtag_trends
from app_twitter.views.tweet import *

app_name = 'app_twitter'

router = routers.DefaultRouter()

router.register('profile', ProfileViewSet)
router.register('', TweetViewSet)

urlpatterns = [
    path('mentions/<int:pk>/', TweetMentions.as_view(), name='mentions'),
    path('retweets/<int:pk>/', TweetRetweets.as_view(), name='retweets'),
    path('quotes/<int:pk>/', TweetQuotes.as_view(), name='quotes'),
    path('likes/<int:pk>/', TweetLikes.as_view(), name='likes'),
    path('vote/<int:pk>/', TweetVote.as_view(), name='vote'),

    path('hashtag/<str:name>/', HashTagRetrieveView.as_view(), name='hashtag'),

    path('profile/<str:username>/followers/', followers, name='profile_followers'),
    path('profile/<str:username>/followings/', followings, name='profile_followings'),
    path('profile/<str:username>/statics/', statics, name='profile_statics'),
    path('profile/<str:username>/tweets/', profile_tweets, name='profile_tweets'),
    path('profile/notifications/count/', notifications_count, name='notifications_count'),
    path('profile/notifications/', notifications, name='notifications'),
    path('profile/block_list/', profile_blocked, name='profile_blocked'),

    path('search/', twitter_search, name='twitter_search'),
    path('search/usernames/', username_search_view, name='search_usernames'),
    path('search/hashtags/', hashtag_search_view, name='search_hashtags'),

    path('trends/hashtags/', hashtag_trends, name='trend_hashtags'),
    path('trends/profiles/', trend_profiles, name='trend_profiles'),

    path('chat/read_message/', read_message, name='read_message'),
    path('chat/read_conversation/', read_conversation, name='read_conversation'),
    path('chat/send_message/', send_message, name='message_sender'),
    path('chat/conversations/', ConversationAPIView.as_view({'get': 'list'}), name='conversations_list'),
    path('chat/conversations/<uuid:pk>/', ConversationAPIView.as_view({'get': 'retrieve'}),
         name='conversations_detail'),
    path('chat/conversations/<uuid:pk>/messages/', ConversationAPIView.as_view({'get': 'messages'}),
         name='conversations_messages'),

    path('vote/', include('app_vote.urls')),

    path('', include(router.urls)),
]
