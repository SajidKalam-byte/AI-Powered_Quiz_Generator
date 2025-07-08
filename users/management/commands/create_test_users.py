from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Create test users for development'

    def handle(self, *args, **options):
        # Create test users if they don't exist
        test_users = [
            {
                'username': 'admin',
                'password': 'admin123',
                'full_name': 'Admin User',
                'email': 'admin@example.com',
                'role': 'admin',
                'is_staff': True,
                'is_superuser': True,
            },
            {
                'username': 'teacher1',
                'password': 'teacher123',
                'full_name': 'Teacher One',
                'email': 'teacher1@example.com',
                'role': 'teacher',
                'teacher_email': 'teacher1@example.com',
            },
            {
                'username': 'student1',
                'password': 'student123',
                'full_name': 'Student One',
                'email': 'student1@example.com',
                'role': 'student',
                'student_roll_no': 'student1',
                'academic_year': '2024-2025',
            },
        ]

        for user_data in test_users:
            username = user_data['username']
            if not User.objects.filter(username=username).exists():
                try:
                    if user_data.get('is_superuser'):
                        user = User.objects.create_superuser(
                            username=user_data['username'],
                            password=user_data['password'],
                            full_name=user_data['full_name'],
                            email=user_data['email'],
                            role=user_data['role']
                        )
                    else:
                        user = User.objects.create_user(
                            username=user_data['username'],
                            password=user_data['password'],
                            full_name=user_data['full_name'],
                            email=user_data['email'],
                            role=user_data['role'],
                            student_roll_no=user_data.get('student_roll_no'),
                            academic_year=user_data.get('academic_year'),
                            teacher_email=user_data.get('teacher_email'),
                        )
                    self.stdout.write(self.style.SUCCESS(f'Created {user_data["role"]} user: {username}'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Error creating user {username}: {e}'))
            else:
                self.stdout.write(self.style.WARNING(f'User {username} already exists'))

        self.stdout.write(self.style.SUCCESS('\nTest users created successfully!'))
        self.stdout.write(self.style.SUCCESS('You can now login with:'))
        self.stdout.write(self.style.SUCCESS('- Admin: admin / admin123'))
        self.stdout.write(self.style.SUCCESS('- Teacher: teacher1 / teacher123'))
        self.stdout.write(self.style.SUCCESS('- Student: student1 / student123'))
