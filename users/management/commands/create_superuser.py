from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

User = get_user_model()

class Command(BaseCommand):
    help = 'Create a superuser for the QuizHub application'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, help='Username for the superuser')
        parser.add_argument('--password', type=str, help='Password for the superuser')
        parser.add_argument('--full-name', type=str, help='Full name for the superuser')
        parser.add_argument('--email', type=str, help='Email for the superuser')

    def handle(self, *args, **options):
        username = options.get('username')
        password = options.get('password')
        full_name = options.get('full_name')
        email = options.get('email')

        # Interactive input if not provided
        if not username:
            username = input('Username: ')
        if not password:
            password = input('Password: ')
        if not full_name:
            full_name = input('Full Name: ')
        if not email:
            email = input('Email (optional): ')

        # Validate required fields
        if not username or not password or not full_name:
            self.stdout.write(self.style.ERROR('Username, password, and full name are required.'))
            return

        # Check if user already exists
        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.ERROR(f'User with username "{username}" already exists.'))
            return

        try:
            # Create superuser
            user = User.objects.create_superuser(
                username=username,
                password=password,
                full_name=full_name,
                email=email if email else None,
                role='admin'
            )
            self.stdout.write(self.style.SUCCESS(f'Superuser "{username}" created successfully.'))
            self.stdout.write(self.style.SUCCESS(f'User can now access Django admin at /admin/ and Admin Dashboard at /admin-dashboard/'))
        except ValidationError as e:
            self.stdout.write(self.style.ERROR(f'Error creating superuser: {e}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error creating superuser: {e}'))
