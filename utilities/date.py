from datetime import timedelta

from django.utils import timezone
from django.utils.timezone import localdate  # noqa


def get_n_unit_ago(**kwargs):
    today = timezone.now()
    n_hour_ago = today - timedelta(**kwargs)
    return n_hour_ago
