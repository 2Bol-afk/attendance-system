from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

User = get_user_model()

class EmailOrUsernameBackend(ModelBackend):
    """
    Authenticate using either username or email.
    If first_login=True, allow login without password.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            try:
                user = User.objects.get(email=username)
            except User.DoesNotExist:
                return None

        # Allow first login without password
        if getattr(user, 'first_login', False):
            return user

        # Otherwise check password
        if user.check_password(password):
            return user

        return None
