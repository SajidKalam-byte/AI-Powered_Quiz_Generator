#!/usr/bin/env python
"""
Test script to verify login functionality
"""
import os
import sys
import django

# Add the project root to the path
sys.path.insert(0, os.path.abspath('.'))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'quizhub.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from django.urls import reverse

def test_login_flow():
    print("Testing login flow...")
    
    User = get_user_model()
    client = Client()
    
    # Test teacher login
    print("1. Testing teacher login...")
    response = client.post(reverse('users:login'), {
        'username': 'teacher1',
        'password': 'teacher123'
    })
    
    print(f"   Login response status: {response.status_code}")
    if response.status_code == 302:
        print(f"   Redirect location: {response.get('Location', 'None')}")
    
    # Test if user is authenticated
    user_id = client.session.get('_auth_user_id')
    print(f"   User authenticated: {user_id is not None}")
    
    if user_id:
        user = User.objects.get(pk=user_id)
        print(f"   Logged in user: {user.username} (role: {user.role})")
        
        # Test access to upload page
        print("2. Testing upload page access...")
        response = client.get('/textprocessor/upload/')
        print(f"   Upload page status: {response.status_code}")
        
        if response.status_code == 200:
            print("   ✓ Upload page accessible!")
        else:
            print(f"   ✗ Upload page not accessible: {response.status_code}")
    else:
        print("   ✗ Login failed!")

if __name__ == '__main__':
    test_login_flow()
