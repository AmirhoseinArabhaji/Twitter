import datetime

from django.utils import timezone
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from app_vote.models import Choice, Vote, VoteChoices, UserVoteHistory


class ChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Choice
        fields = (
            'id',
            'title',
            'count',
        )


class VoteSerializer(serializers.ModelSerializer):
    choices = ChoiceSerializer(many=True, required=True)

    expire_day = serializers.IntegerField(min_value=0, max_value=7, required=True, write_only=True)
    expire_hour = serializers.IntegerField(min_value=0, max_value=23, required=True, write_only=True)
    expire_minutes = serializers.IntegerField(min_value=0, max_value=59, required=True, write_only=True)

    is_expired = serializers.SerializerMethodField(read_only=True)

    participated = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Vote
        fields = (
            'id',
            'choices',
            'expire_day',
            'expire_hour',
            'expire_minutes',
            'expire_date',
            'is_expired',
            'participated',
        )
        read_only_fields = (
            'id',
            'expire_date',
        )

    @staticmethod
    def get_is_expired(instance):
        return instance.expire_date < timezone.now()

    def get_participated(self, instance):
        user = self.context['request'].user
        if user.is_authenticated:
            history = UserVoteHistory.objects.filter(vote=instance, user=user).cache().first()
            return history.choice.id if history else None
        else:
            return None

    def create(self, validated_data):
        validated_data['owner'] = self.context['request'].user
        choices = validated_data.pop('choices')

        expire_date = timezone.now() + datetime.timedelta(
            days=validated_data.pop('expire_day', 0),
            hours=validated_data.pop('expire_hour', 0),
            minutes=validated_data.pop('expire_minutes', 0),
        )

        validated_data['expire_date'] = expire_date

        vote = super().create(validated_data)

        for index, choice in enumerate(choices):
            choices[index] = Choice(**choice)

        Choice.objects.bulk_create(choices)

        for choice in choices:
            vote.choices.add(choice)

        return vote

    def to_representation(self, instance: Vote):
        if self.get_is_expired(instance):
            if len(instance.result) == 0:
                choices = instance.choices.all()
                result = list()

                for choice in choices:
                    result.append(ChoiceSerializer(choice).data)
                instance.result = result
                instance.save()
            return {
                'id': instance.id,
                'choices': instance.result,
                'expire_date': instance.expire_date,
                'is_expired': True,
                'participated': self.get_participated(instance),
            }

        else:
            return super().to_representation(instance)


class ChoiceVotingSerializer(serializers.Serializer):
    vote = serializers.PrimaryKeyRelatedField(queryset=Vote.objects.filter(expire_date__gt=now()))
    choice = serializers.UUIDField(required=True, write_only=True)

    class Meta:
        fields = (
            'vote',
            'choice',
        )

    def validate(self, attrs):
        attrs = super().validate(attrs)

        if not VoteChoices.objects.filter(vote=attrs['vote'], choice=attrs['choice']).cache().exists():
            raise ValidationError({'message': _('this choice is not valid for the vote')})

        if UserVoteHistory.objects.filter(vote=attrs['vote'], user=self.context['request'].user).cache().exists():
            raise ValidationError({'message': _('you hav already participated in this vote')})

        return attrs

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass
