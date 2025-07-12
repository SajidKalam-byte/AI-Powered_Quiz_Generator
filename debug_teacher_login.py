#!/usr/bin/env python
"""
Test script to debug teacher login redirect issue
"""

from django.test import Client
from django.urls import reverse
from django.contrib.auth import authenticate
from users.models import CustomUser
import json

print("=== Debugging Teacher Login Issue ===")

# Create a fresh client (simulates new browser session)
client = Client()

print("\n1. Testing teacher authentication...")
user = authenticate(username='teacher1', password='teacher123')
if user:
    print(f"✓ Teacher authenticated successfully")
    print(f"  Role: {user.role}")
    print(f"  Active: {user.is_active}")
    print(f"  Staff: {user.is_staff}")
    print(f"  Superuser: {user.is_superuser}")
else:
    print("✗ Teacher authentication failed")
    exit(1)

print("\n2. Testing login POST request...")
login_response = client.post(reverse('users:login'), {
    'username': 'teacher1',
    'password': 'teacher123'
})

print(f"Login response status: {login_response.status_code}")
print(f"Login response redirect: {login_response.url if login_response.status_code == 302 else 'No redirect'}")

# Check if user is logged in
user_logged_in = client.session.get('_auth_user_id')
print(f"User logged in (session): {user_logged_in is not None}")

print("\n3. Testing dashboard access...")
dashboard_response = client.get('/dashboard/')
print(f"Dashboard response status: {dashboard_response.status_code}")

if dashboard_response.status_code == 302:
    print(f"Dashboard redirects to: {dashboard_response.url}")
    print("This indicates authentication issue or middleware problem")
elif dashboard_response.status_code == 200:
    print("✓ Dashboard loads successfully")
else:
    print(f"Unexpected response: {dashboard_response.status_code}")

print("\n4. Testing direct dashboard access with force_login...")
client.force_login(user)
dashboard_response2 = client.get('/dashboard/')
print(f"Dashboard response (force_login): {dashboard_response2.status_code}")

if dashboard_response2.status_code == 200:
    print("✓ Dashboard works with force_login")
else:
    print(f"✗ Dashboard fails even with force_login: {dashboard_response2.status_code}")

print("\n5. Testing session data...")
print(f"Session keys: {list(client.session.keys())}")
print(f"Session expiry: {client.session.get_expiry_date()}")

print("\n6. Testing middleware bypass...")
# Test if middleware is causing issues
print("Testing URL without middleware interference...")
from django.http import HttpRequest
from django.contrib.auth.models import AnonymousUser
from users.middleware import AuthenticationMiddleware

# Create a mock request
request = HttpRequest()
request.path = '/dashboard/'
request.user = user
request.method = 'GET'
request.session = {}

# Create mock get_response
def mock_get_response(request):
    return "OK"

middleware = AuthenticationMiddleware(mock_get_response)
try:
    result = middleware(request)
    print(f"Middleware result: {result}")
except Exception as e:
    print(f"Middleware error: {e}")

print("\n=== Summary ===")
print("If you see 'Dashboard redirects to: /?next=/dashboard/', the issue is:")
print("1. Session not being maintained between requests")
print("2. Middleware rejecting authenticated users")
print("3. Authentication state not being properly set")
print("\nTo fix: Clear browser cache, cookies, or try incognito mode")
