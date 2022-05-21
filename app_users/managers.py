from django.conf import settings
from django.contrib.auth.base_user import BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _


class UserQuerySet(models.QuerySet):

    def activated(self):
        return self.filter(is_active=True)


class UserManager(BaseUserManager):
    def get_queryset(self):
        return UserQuerySet(self.model, using=self._db)

    def _create_user(self, username, password, is_superuser, is_active, is_staff, email=None, phone=None,
                     **extra_fields):
        if not email and not phone:
            raise ValueError(_('Email or phone is required.'))

        if not username:
            raise ValueError(_('Users must choose username.'))

        if isinstance(email, str):
            email = self.normalize_email(email)

        _type = self.model.UserTypes.NORMAL

        if is_superuser:
            _type = self.model.UserTypes.SUPERUSER

        elif is_staff:
            _type = self.model.UserTypes.STAFF

        user_obj = self.model(
            username=username,
            email=email,
            phone=phone,
            is_active=is_active,
            type=_type,
            **extra_fields,
        )
        user_obj.set_password(password)
        user_obj.save()

        return user_obj

    def activated(self):
        return self.get_queryset().activated()

    def create_user(self, username, password, email=None, phone=None, **extra_fields):
        return self._create_user(username, password, False, False, False, email, phone, **extra_fields)

    def create_pre_active_user(self, username, password, email=None, phone=None, **extra_fields):
        return self._create_user(username, password, False, True, False, email, phone, **extra_fields)

    def create_superuser(self, username, password, email=None, phone=None, **extra_fields):
        return self._create_user(username, password, True, True, True, email, phone, **extra_fields)
