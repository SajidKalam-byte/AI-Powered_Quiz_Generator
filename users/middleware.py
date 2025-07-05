from pyexpat.errors import messages
from django.shortcuts import redirect
from django.urls import reverse
from django.conf import settings
import datetime


class AuthenticationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Skip middleware for login, logout, and registration pages
        public_urls = [
            reverse('users:login'),
            reverse('users:student_register'),
            reverse('users:teacher_register'),
        ]

        if request.path in public_urls or request.path.startswith(settings.STATIC_URL) or request.path.startswith(settings.MEDIA_URL):
            return self.get_response(request)

        # Check if user is authenticated
        if not request.user.is_authenticated:
            # Preserve the 'next' parameter to redirect after login
            login_url = reverse('users:login')
            next_param = request.GET.get('next', request.path)
            return redirect(f"{login_url}?next={next_param}")

        # Session timeout check
        if request.user.is_authenticated and 'last_activity' in request.session:
            last_activity = datetime.datetime.fromisoformat(request.session['last_activity'])
            if (datetime.datetime.now(datetime.timezone.utc) - last_activity).total_seconds() > settings.SESSION_COOKIE_AGE:
                from django.contrib.auth import logout
                logout(request)
                messages.error(request, "Your session has expired. Please log in again.")
                login_url = reverse('users:login')
                next_param = request.GET.get('next', request.path)
                return redirect(f"{login_url}?next={next_param}")

        # Update last activity
        request.session['last_activity'] = str(datetime.datetime.now(datetime.timezone.utc))

        return self.get_response(request)