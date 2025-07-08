#!/usr/bin/env python
"""
Debug script to check user roles and permissions
Run with: python manage.py shell < debug_users.py
"""

from users.models import CustomUser
from django.db.models import Q

print("=== User Debug Information ===")
print()

# Get all users
users = CustomUser.objects.all()

if not users.exists():
    print("No users found in the database.")
else:
    print(f"Total users: {users.count()}")
    print()
    
    for user in users:
        print(f"Username: {user.username}")
        print(f"Full Name: {user.full_name}")
        print(f"Role: {getattr(user, 'role', 'No role attribute')}")
        print(f"Is Staff: {user.is_staff}")
        print(f"Is Superuser: {user.is_superuser}")
        print(f"Is Active: {user.is_active}")
        print(f"Date Joined: {user.date_joined}")
        print("-" * 40)

print()
print("=== Admin Users ===")
admin_users = users.filter(
    Q(is_staff=True) | Q(is_superuser=True) | Q(role='admin')
)

if admin_users.exists():
    for user in admin_users:
        print(f"- {user.username} (staff: {user.is_staff}, super: {user.is_superuser}, role: {getattr(user, 'role', 'None')})")
else:
    print("No admin users found.")

print()
print("=== Creating a test admin user ===")
try:
    admin_user, created = CustomUser.objects.get_or_create(
        username='test_admin',
        defaults={
            'full_name': 'Test Admin',
            'email': 'admin@test.com',
            'role': 'admin',
            'is_staff': True,
            'is_superuser': True,
        }
    )
    if created:
        admin_user.set_password('admin123')
        admin_user.save()
        print("✓ Created test admin user: test_admin / admin123")
    else:
        print("✓ Test admin user already exists")
except Exception as e:
    print(f"✗ Error creating admin user: {e}")
