from django.shortcuts import render, redirect
from django.conf import settings
import os
from datetime import datetime

def home(request):
    """
    Home page view that redirects authenticated users to dashboard
    and shows landing page for unauthenticated users.
    """
    if request.user.is_authenticated:
        return redirect('users:dashboard')
    
    # Render landing page with comprehensive documentation
    md_path = os.path.join(settings.BASE_DIR, 'COMPREHENSIVE_DOCUMENTATION.md')
    try:
        with open(md_path, 'r', encoding='utf-8') as f:
            documentation = f.read()
    except FileNotFoundError:
        documentation = "Documentation not available."
    
    context = {
        'documentation': documentation,
        'current_year': datetime.now().year,
    }
    return render(request, 'core/home.html', context)
