from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.shortcuts import redirect


def role_required(allowed_roles=[]):
    """
    Decorator to restrict access based on user role.
    """
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(request, "You must be logged in to access this page.")
                return redirect('users:login')

            if request.user.role not in allowed_roles:
                messages.error(request, "You do not have permission to access this page.")
                return redirect('users:dashboard')

            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator