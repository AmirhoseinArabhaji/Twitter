from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny

from app_twitter.models import Hashtag
from app_twitter.serializers.tweet import HashtagSerializer


class SearchHashTags(ListAPIView):
    queryset = Hashtag.objects.all()

    serializer_class = HashtagSerializer
    permission_classes = (AllowAny,)

    def get_queryset(self):
        search_term = self.request.query_params.get('q')
        if search_term:
            return super().get_queryset().filter(name__contains=search_term).cache()
        else:
            return Hashtag.objects.none()
