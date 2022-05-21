from django.db import transaction
from django.db.models import F
from django.utils.decorators import method_decorator
from rest_framework.generics import UpdateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from app_vote.models import Choice, UserVoteHistory
from app_vote.permissions import *
from app_vote.serializers import ChoiceVotingSerializer, VoteSerializer


class VoteUpdateAPIView(UpdateAPIView):
    queryset = Choice.objects.none()
    permission_classes = [
        IsAuthenticated,
        UsernameIsActive,
        IsPrivate,
        IsBlocked,
        BlockedYou,
    ]

    serializer_class = ChoiceVotingSerializer

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        choice = Choice.objects.select_for_update().get(pk=serializer.validated_data['choice'])

        choice.count = F('count') + 1
        choice.save()

        UserVoteHistory.objects.create(user=request.user, vote=serializer.validated_data['vote'], choice=choice)

        return Response(
            data=VoteSerializer(instance=serializer.validated_data['vote'], context={'request': request}).data)
