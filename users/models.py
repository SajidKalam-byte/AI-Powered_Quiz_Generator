from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models

class CustomUserManager(BaseUserManager):
    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError("Username (Student Roll No or Email) is required")
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, username, password, **extra_fields):
        extra_fields.setdefault('role', 'admin')
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(username, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    
    ROLE_CHOICES = (
        ('student', 'Student'),
        ('teacher', 'Teacher'),
        ('admin', 'Superadmin'),
    )
    
    username = models.CharField(max_length=150, unique=True)  # Student Roll No or Email for Teachers
    email = models.EmailField(blank=True, null=True)
    full_name = models.CharField(max_length=255)
    
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    
    # Student Specific Fields
    student_roll_no = models.CharField(max_length=50, blank=True, null=True, unique=True)
    academic_year = models.CharField(max_length=50, blank=True, null=True)
    
    # Teacher Specific Fields
    teacher_email = models.EmailField(blank=True, null=True, unique=True)
    
    # Common Fields
    date_joined = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)  # Required for Django admin access
    
    # Future Profile/Results/Score fields can be added here
    
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return f"{self.full_name} ({self.role})"
