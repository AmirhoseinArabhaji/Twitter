import uuid

from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.contrib.postgres.indexes import HashIndex
from django.db import models
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _

from app_users.managers import UserManager


def user_avatar_upload_path(instance, filename):
    return f"profile/{instance.phone}/avatar/{uuid.uuid4().hex}.{filename.split('.')[-1]}"


def user_header_upload_path(instance, filename):
    return f"profile/{instance.phone}/header/{uuid.uuid4().hex}.{filename.split('.')[-1]}"


class User(AbstractBaseUser, PermissionsMixin):
    class UserTypes(models.TextChoices):
        NORMAL = ('NORMAL', _('normal user'))
        STAFF = ('STAFF', _('staff user'))
        SUPERUSER = ('SUPERUSER', _('super user'))

    type = models.CharField(max_length=64, choices=UserTypes.choices, default=UserTypes.NORMAL, db_index=True)

    is_active = models.BooleanField(_('active'), default=False)
    is_private = models.BooleanField(_('private'), default=False)
    is_ban = models.BooleanField(_('ban'), default=False)

    email = models.EmailField(_('email address'), unique=True, null=True)
    phone = models.CharField(_('mobile number'), max_length=11, unique=True, null=True)
    fullname = models.CharField(_('full name'), max_length=128, null=True)

    username = models.CharField(_('username'), max_length=26, unique=True)
    password = models.CharField(_('password'), max_length=128)

    avatar = models.ImageField(upload_to=user_avatar_upload_path, null=True, blank=True)
    header = models.ImageField(upload_to=user_header_upload_path, null=True, blank=True)
    bio = models.CharField(_('tweeter bio'), max_length=256, blank=True, null=True)

    birth_date = models.DateField(_('birth date'))

    metadata = models.JSONField(null=True, blank=True)

    date_joined = models.DateTimeField(_('date joined'), default=now)

    USERNAME_FIELD = 'username'
    EMAIL_FIELD = 'email'
    LOGIN_WITH_THESE_FIELDS = (USERNAME_FIELD, EMAIL_FIELD,)

    objects = UserManager()

    class Meta:
        ordering = ('-date_joined',)

        verbose_name = _('user')
        verbose_name_plural = _('users')
        indexes = [
            HashIndex(fields=('phone',)),
            HashIndex(fields=('email',)),
            HashIndex(fields=('username',)),
        ]

    def save(self, *args, **kwargs):
        if self.username:
            self.username = str.lower(self.username)

        return super().save(*args, **kwargs)

    @property
    def is_superuser(self):
        return self.type == self.UserTypes.SUPERUSER

    @property
    def is_staff(self):
        if self.type in [self.UserTypes.STAFF, self.UserTypes.SUPERUSER]:
            return True
        return False
