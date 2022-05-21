import datetime

from django.contrib.contenttypes.models import ContentType
from django.db.models import Count, DateField
from django.db.models.functions import Cast
from django.utils.timezone import make_aware
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from app_like.models import Like
from app_twitter.models import Tweet, Hashtag, Fellowship
from utilities.date import get_n_unit_ago
from utilities.pagination import PageNumberPagination


class TwitterStatistics(ListAPIView):
    queryset = Tweet.objects.none()
    serializer_class = None
    permission_classes = (IsAdminUser,)
    pagination_class = PageNumberPagination

    def list(self, request, *args, **kwargs):
        # TODO: Caching Statistics to a database model

        today_beginning = make_aware(datetime.datetime.combine(datetime.date.today(), datetime.time.min))
        today_end = make_aware(datetime.datetime.combine(datetime.date.today(), datetime.time.max))

        today_statistics = {
            "likes_count": Like.objects.filter(
                content_type=ContentType.objects.get_for_model(model=Tweet),
                created_at__range=[today_beginning, today_end]).cache().count(),

            "tweets_count": Tweet.objects.filter(created_at__range=[today_beginning, today_end]).cache().count(),
            "hashtags_count": Hashtag.objects.filter(updated_at__range=[today_beginning, today_end]).cache().count(),
            "following_count": Fellowship.objects.filter(
                created_at__range=[today_beginning, today_end]).cache().count(),
        }

        thirty_days_ago = make_aware(datetime.datetime.combine(get_n_unit_ago(days=30), datetime.time.min))

        tweets_chart = Tweet.objects.all().filter(created_at__range=[thirty_days_ago, today_end]). \
            annotate(date=Cast('created_at', DateField())).values('date'). \
            annotate(count=Count('date')).values('date', 'count').order_by().cache()

        hashtags_chart = Hashtag.objects.all().filter(updated_at__range=[thirty_days_ago, today_end]). \
            annotate(date=Cast('updated_at', DateField())).values('date'). \
            annotate(count=Count('date')).values('date', 'count').order_by().cache()

        likes_chart = Like.objects.filter(
            content_type=ContentType.objects.get_for_model(model=Tweet),
            created_at__range=[thirty_days_ago, today_end]). \
            annotate(date=Cast('created_at', DateField())).values('date'). \
            annotate(count=Count('date')).values('date', 'count').order_by().cache()

        followings_chart = Fellowship.objects.filter(
            created_at__range=[thirty_days_ago, today_end]). \
            annotate(date=Cast('created_at', DateField())).values('date'). \
            annotate(count=Count('date')).values('date', 'count').order_by().cache()

        charts_data = {
            'tweets': list(
                tweets_chart
            ),
            'likes': list(
                likes_chart
            ),
            'hashtags': list(
                hashtags_chart
            ),
            'followings': list(
                followings_chart
            ),
        }

        return Response(data={
            'today': today_statistics,
            'thirty_days_ago': charts_data,
        })


twitter_statistics = TwitterStatistics.as_view()

__all__ = [
    'twitter_statistics',
]
