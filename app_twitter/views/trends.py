import math

from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny

from app_twitter.models import Hashtag
from app_twitter.serializers.hashtag import HashTagSerializer
from utilities.date import get_n_unit_ago


class SearchHashTags(ListAPIView):
    TIMEFRAMES = {
        'd': 1,
        'w': 7,
        'm': 30,
        'y': 365
    }

    queryset = Hashtag.objects.all()
    Hashtag.objects.filter()
    serializer_class = HashTagSerializer
    permission_classes = (AllowAny,)

    def get_queryset(self):
        count = self.request.query_params.get('count', 20)
        time_frame = self.request.query_params.get('time_frame', 'w')

        time_filter = self.TIMEFRAMES.get(time_frame, 'w')

        queryset = super().get_queryset().filter(updated_at__gt=get_n_unit_ago(days=time_filter)).cache()

        if count and type(count) is int:
            count = int(min(math.fabs(count), 20))
            return queryset[:count]
        else:
            return queryset[:20]


hashtag_trends = SearchHashTags.as_view()

__all__ = [
    'hashtag_trends',
]
