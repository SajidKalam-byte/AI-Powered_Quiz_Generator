#!/usr/bin/env python
"""
Simple test script to verify the template selection works correctly
"""
import os
import sys
import django

# Add the project root to the path
sys.path.insert(0, os.path.abspath('.'))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'quizhub.settings')
django.setup()

from users.models import CustomUser
from quizzes.views import get_dashboard_template

def test_template_selection():
    print("Testing template selection for different user roles...")
    
    # Test with different user roles
    try:
        # Get existing users
        users = CustomUser.objects.all()
        print(f"Found {users.count()} users")
        
        for user in users:
            template = get_dashboard_template(user)
            print(f"User: {user.username} (Role: {user.role}) -> Template: {template}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    test_template_selection()
