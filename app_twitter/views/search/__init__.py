from django.contrib.auth import get_user_model
from django.db.models import Q
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from app_twitter.models import Hashtag
from app_twitter.serializers.profile import TwitterUsernameSearchResult
from app_twitter.serializers.tweet import HashtagSerializer
from app_twitter.views.search.hashtags import SearchHashTags
from app_twitter.views.search.usernames import SearchUsernames

User = get_user_model()


class SearchTwitter(ListAPIView):
    queryset = None
    serializer_class = None
    permission_classes = (AllowAny,)
    MAX_RESULT_COUNT = 10

    def get_queryset(self):
        search_term = self.request.query_params.get('q', None)
        user_only = self.request.query_params.get('user_only', None)
        if search_term:
            hashtags_qs = []
            users_qs = User.objects.filter(Q(fullname__icontains=search_term) | Q(username__icontains=search_term))[
                       :self.MAX_RESULT_COUNT].only('username', 'fullname').cache()

            if user_only != '1':
                hashtags_qs = Hashtag.objects.filter(name__icontains=search_term)[:self.MAX_RESULT_COUNT].only(
                    'name').cache()

                if len(hashtags_qs) + len(users_qs) > self.MAX_RESULT_COUNT:
                    if len(hashtags_qs) > len(users_qs):
                        users_qs = users_qs[:self.MAX_RESULT_COUNT - len(hashtags_qs)]
                    else:
                        hashtags_qs = hashtags_qs[:self.MAX_RESULT_COUNT - len(users_qs)]

            return {
                'hashtag': hashtags_qs,
                'user': users_qs
            }

        else:
            return {}

    def list(self, request, *args, **kwargs):
        query_sets = self.get_queryset()
        result = dict()

        for key, qs in query_sets.items():
            if key == 'hashtag':
                result[key] = HashtagSerializer(qs, many=True, context={'request': self.request}).data
            elif key == 'user':
                result[key] = TwitterUsernameSearchResult(qs, many=True, context={'request': self.request}).data
        return Response(data=result)


hashtag_search_view = SearchHashTags.as_view()
username_search_view = SearchUsernames.as_view()
twitter_search = SearchTwitter.as_view()

__all__ = [
    'hashtag_search_view',
    'username_search_view',
    'twitter_search',
]
