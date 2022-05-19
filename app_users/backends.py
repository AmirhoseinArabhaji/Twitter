from django.contrib.auth import backends, get_user_model

User = get_user_model()


class PasswordAuthenticationBackend(backends.ModelBackend):
    def authenticate(self, request, username=None, phone=None, email=None, password=None, **kwargs):

        if username or phone or email:
            if phone:
                user_lookup_dict = {'phone': phone}
            elif username:
                user_lookup_dict = {'username': username}
            elif email:
                user_lookup_dict = {'email': email}

            try:
                user = User._default_manager.get(**user_lookup_dict)

                if not user.password:
                    return None

            except User.DoesNotExist:
                pass
            else:
                if user.check_password(password) and self.user_can_authenticate(user):
                    return user
