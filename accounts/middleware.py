# accounts/middleware.py
from django.shortcuts import redirect
from django.urls import reverse

class FirstLoginMiddleware:
    """
    Redirect users to change password if first_login=True,
    but exclude superusers, login page, change-password page, admin, and static files.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Only apply if user is authenticated
        user = request.user
        if user.is_authenticated:
            # Exclude superusers
            if user.is_superuser:
                return self.get_response(request)

            # Excluded paths
            excluded_paths = [
                reverse('accounts:change_password'),  # change password page
                reverse('accounts:login'),           # login page
            ]
            
            if request.path.startswith('/admin/'):
                return self.get_response(request)
            if request.path.startswith('/static/') or request.path.startswith('/media/'):
                return self.get_response(request)
            if request.path in excluded_paths:
                return self.get_response(request)

            # Redirect first-login users
            if getattr(user, 'first_login', False):
                return redirect('accounts:change_password')

        response = self.get_response(request)
        return response
