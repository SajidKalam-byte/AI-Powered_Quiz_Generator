#!/usr/bin/env python
"""
Script to test passwords for existing users
"""

from users.models import CustomUser
from django.contrib.auth import authenticate

print("=== Testing Passwords for Existing Users ===")

users = ['admin', 'student1', 'teacher1']
passwords = ['password123', 'admin123', 'admin', 'student123', 'teacher123']

for username in users:
    print(f"\nTesting user: {username}")
    try:
        user = CustomUser.objects.get(username=username)
        print(f"  User exists: {user.full_name}")
        
        password_found = False
        for pwd in passwords:
            auth = authenticate(username=username, password=pwd)
            if auth:
                print(f"  ✓ Password: {pwd}")
                password_found = True
                break
        
        if not password_found:
            print("  ✗ No password found in test set")
            
    except CustomUser.DoesNotExist:
        print(f"  ✗ User does not exist")

print("\n=== Resetting Password for admin user ===")
try:
    admin_user = CustomUser.objects.get(username='admin')
    admin_user.set_password('admin123')
    admin_user.save()
    print("✓ Password reset to 'admin123' for admin user")
    
    # Test authentication
    auth = authenticate(username='admin', password='admin123')
    if auth:
        print("✓ Authentication successful")
    else:
        print("✗ Authentication failed")
        
except Exception as e:
    print(f"✗ Error: {e}")
