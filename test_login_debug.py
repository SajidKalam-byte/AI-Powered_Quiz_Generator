#!/usr/bin/env python
"""
Test script to simulate login process and check redirection
Run with: python manage.py shell -c "exec(open('test_login_debug.py').read())"
"""

from django.test import Client
from django.urls import reverse
from users.models import CustomUser
from django.contrib.auth import authenticate

print("=== Testing Login Process ===")
print()

# Create a test client
client = Client()

# Test users
test_users = [
    {'username': 'admin', 'role': 'admin'},
    {'username': 'student1', 'role': 'student'},
    {'username': 'teacher1', 'role': 'teacher'},
    {'username': 'test_admin', 'role': 'admin'},
]

for user_info in test_users:
    username = user_info['username']
    expected_role = user_info['role']
    
    print(f"Testing user: {username}")
    
    # Check if user exists
    try:
        user = CustomUser.objects.get(username=username)
        print(f"✓ User exists: {user.username}")
        print(f"  Role: {user.role}")
        print(f"  Is Staff: {user.is_staff}")
        print(f"  Is Superuser: {user.is_superuser}")
        print(f"  Is Active: {user.is_active}")
    except CustomUser.DoesNotExist:
        print(f"✗ User {username} does not exist")
        continue
    
    # Test authentication
    test_password = 'admin123' if username == 'test_admin' else 'password123'
    auth_user = authenticate(username=username, password=test_password)
    
    if auth_user:
        print(f"✓ Authentication successful")
        
        # Test login via client
        response = client.post(reverse('users:login'), {
            'username': username,
            'password': test_password
        })
        
        print(f"  Login response status: {response.status_code}")
        print(f"  Redirect URL: {response.url if response.status_code == 302 else 'No redirect'}")
        
        # Check where admin users should be redirected
        if user.role == 'admin' or user.is_staff or user.is_superuser:
            expected_redirect = reverse('admin_dashboard:dashboard')
            print(f"  Expected redirect for admin: {expected_redirect}")
        else:
            expected_redirect = reverse('users:dashboard')
            print(f"  Expected redirect for {user.role}: {expected_redirect}")
            
        # Test direct access to admin dashboard
        if user.role == 'admin' or user.is_staff or user.is_superuser:
            admin_response = client.get(reverse('admin_dashboard:dashboard'))
            print(f"  Admin dashboard access: {admin_response.status_code}")
            if admin_response.status_code != 200:
                print(f"    Error accessing admin dashboard: {admin_response.status_code}")
        
        # Logout for next test
        client.logout()
    else:
        print(f"✗ Authentication failed for {username}")
    
    print("-" * 50)

print()
print("=== Testing Django Admin Access ===")

# Test Django admin access
print("Testing /admin/ URL...")
admin_response = client.get('/admin/')
print(f"Admin URL response: {admin_response.status_code}")
print(f"Admin URL redirect: {admin_response.url if admin_response.status_code == 302 else 'No redirect'}")

print("Testing /admin/login/ URL...")
admin_login_response = client.get('/admin/login/')
print(f"Admin login URL response: {admin_login_response.status_code}")
print(f"Admin login URL redirect: {admin_login_response.url if admin_login_response.status_code == 302 else 'No redirect'}")

print()
print("=== Summary ===")
print("If you see any issues above, they indicate the source of your login problems.")
print("Common issues:")
print("- Authentication failures indicate wrong passwords")
print("- Redirect loops indicate middleware or URL configuration issues")
print("- 404 errors indicate missing URL patterns or views")
print("- 500 errors indicate server errors in views or templates")
