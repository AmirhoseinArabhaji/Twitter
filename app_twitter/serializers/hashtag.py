from enum import Enum

from rest_framework import serializers

from app_twitter.models import Hashtag


class CountUnites(Enum):
    K = 1000, 'K'
    M = 1_000_000, 'M'


class HashTagSerializer(serializers.ModelSerializer):
    count = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Hashtag
        fields = (
            'name',
            'count',
        )

        read_only_fields = fields

    @staticmethod
    def get_count(instance):
        count = instance.usage_count
        if CountUnites.K.value[0] <= count <= CountUnites.M.value[0]:
            count = str(round(count / CountUnites.K.value[0], 2))
            return f'{count}{CountUnites.K.name}'

        elif count >= CountUnites.M.value[0]:
            count = str(round(count / CountUnites.M.value[0], 2))
            return f'{count}{CountUnites.M.name}'
        else:
            return count
