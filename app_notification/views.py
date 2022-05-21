from django.db import transaction
from django.utils.timezone import now
from rest_framework import status
from rest_framework.generics import UpdateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from app_notification.models import Notification
from app_notification.serializers import ReadingNotificationSerializer


class ReadNotificationView(UpdateAPIView):
    queryset = Notification.objects.all()
    serializer_class = ReadingNotificationSerializer
    permission_classes = [
        IsAuthenticated,
    ]

    http_method_names = ['put']
    lookup_field = 'id'

    def get_queryset(self):
        return super().get_queryset().filter(performed_on=self.request.user, read_at__isnull=True)

    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        _id = serializer.validated_data['id']

        qs = self.get_queryset().filter(id=_id)

        if qs.exists():
            with transaction.atomic():
                instance = qs.select_for_update().first()
                instance.read_at = now()
                instance.save()

        return Response(status=status.HTTP_200_OK)


read_notification = ReadNotificationView.as_view()

__all__ = [
    'read_notification',
]
