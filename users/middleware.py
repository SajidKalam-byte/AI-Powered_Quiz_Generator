from django.shortcuts import redirect
from django.urls import reverse
from django.conf import settings
from django.contrib import messages
import datetime
import logging

logger = logging.getLogger(__name__)


class AuthenticationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Skip middleware for certain paths
        public_urls = [
            '/',  # Allow landing page
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

        # Allow public URLs (including POST requests to login) and static/media files
        if request.path in public_urls or request.path.startswith(settings.STATIC_URL) or request.path.startswith(settings.MEDIA_URL):
            return self.get_response(request)

        # Check if user is authenticated - only redirect to login for protected URLs
        if not request.user.is_authenticated:
            # Only redirect to login if this is a protected path
            # Skip redirecting for landing page and other public paths
            if request.path != '/':
                login_url = reverse('users:login')
                return redirect(login_url)

        # Simplified session timeout check - only check every 30 seconds to reduce overhead
        if (request.user.is_authenticated and 
            'last_activity' in request.session and 
            'last_timeout_check' not in request.session):
            
            try:
                last_activity = datetime.datetime.fromisoformat(request.session['last_activity'])
                current_time = datetime.datetime.now(datetime.timezone.utc)
                
                # Only check timeout if it's been more than 30 seconds since last check
                if (current_time - last_activity).total_seconds() > settings.SESSION_COOKIE_AGE:
                    from django.contrib.auth import logout
                    logout(request)
                    messages.error(request, "Your session has expired. Please log in again.")
                    login_url = reverse('users:login')
                    return redirect(login_url)
                
                # Mark that we've checked timeout recently
                request.session['last_timeout_check'] = str(current_time)
                
            except (ValueError, TypeError) as e:
                logger.warning(f"Invalid datetime format in session: {e}")
                # Clear invalid session data
                request.session.pop('last_activity', None)

        # Update last activity for authenticated users (less frequently)
        if request.user.is_authenticated:
            current_time = datetime.datetime.now(datetime.timezone.utc)
            last_activity = request.session.get('last_activity')
            
            # Only update activity timestamp if it's been more than 60 seconds
            if (not last_activity or 
                (current_time - datetime.datetime.fromisoformat(last_activity)).total_seconds() > 60):
                request.session['last_activity'] = str(current_time)

        return self.get_response(request)