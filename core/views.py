from django.shortcuts import render, redirect
from django.conf import settings

def home(request):
    """
    Home page view that redirects authenticated users to dashboard
    and shows landing page for unauthenticated users.
    """
    if request.user.is_authenticated:
        return redirect('users:dashboard')
    
    return render(request, 'core/home.html')
