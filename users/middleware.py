from django.shortcuts import redirect
from django.urls import reverse
from django.conf import settings
from django.contrib import messages
import datetime


class AuthenticationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Skip middleware for certain paths
        public_urls = [
            reverse('users:login'),
            reverse('users:student_register'),
            reverse('users:teacher_register'),
            '/admin/login/',  # Allow access to Django admin login
        ]

        # Allow access to admin URLs for authenticated admin users
        if request.path.startswith('/admin/'):
            # Always allow access to Django admin login page
            if request.path == '/admin/login/':
                return self.get_response(request)
            # For other admin URLs, check authentication and authorization
            if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser or (hasattr(request.user, 'role') and request.user.role == 'admin')):
                return self.get_response(request)
            elif not request.user.is_authenticated:
                # Redirect to Django admin login for admin URLs (not custom login)
                return redirect(f"/admin/login/?next={request.path}")
            else:
                # User is authenticated but not authorized for admin
                messages.error(request, "You don't have permission to access the admin panel.")
                return redirect('users:dashboard')

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