from django.contrib.auth import get_user_model
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated

from app_twitter.serializers.profile import MinimalProfileSerializer

User = get_user_model()


class SearchUsernames(ListAPIView):
    queryset = User.objects.all()

    serializer_class = MinimalProfileSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        search_term = self.request.query_params.get('q')
        if search_term:
            return super().get_queryset().filter(username__icontains=search_term).cache()
        else:
            return User.objects.none()
