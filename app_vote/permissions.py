from django.contrib.auth import get_user_model
from django.utils.translation import gettext as _
from rest_framework import permissions

from app_twitter.models import Fellowship, BlockList

User = get_user_model()


class IsOwnerOrReadOnly(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        else:
            if request.user and request.user.is_authenticated:
                return obj == request.user
            return False


class IsPrivate(permissions.BasePermission):
    message = _('user account is private')

    def has_object_permission(self, request, view, obj):
        if obj.is_private:
            if request.user.is_authenticated:
                return bool(Fellowship.objects.filter(follower=request.user, following=obj).cache().exists())
            else:
                return False
        else:
            return True


class IsBlocked(permissions.BasePermission):
    message = _('user account is blocked')

    def has_object_permission(self, request, view, obj):
        if request.user.is_authenticated:
            return bool(not BlockList.objects.filter(blocked=obj, blocker=request.user).cache().exists())
        else:
            return True


class BlockedYou(permissions.BasePermission):
    message = _('user account blocked you')

    def has_object_permission(self, request, view, obj):
        if request.user.is_authenticated:
            return bool(not BlockList.objects.filter(blocker=obj, blocked=request.user).cache().exists())
        else:
            return True


class UsernameIsActive(permissions.BasePermission):
    message = _('this action is not possible without setting the username')

    def has_permission(self, request, view):
        if request.user.is_authenticated:
            return bool(request.user.username is not None)
        else:
            return True


__all__ = [
    'UsernameIsActive',
    'IsOwnerOrReadOnly',
    'IsPrivate',
    'IsBlocked',
    'BlockedYou',
]
