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
        extra_fields.setdefault('is_active', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
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

    def get_full_name(self):
        """Required for Django admin"""
        return self.full_name

    def get_short_name(self):
        """Required for Django admin"""
        return self.full_name.split()[0] if self.full_name else self.username

    def has_perm(self, perm, obj=None):
        """Required for Django admin"""
        return self.is_superuser

    def has_module_perms(self, app_label):
        """Required for Django admin"""
        return self.is_superuser

    @property
    def is_admin(self):
        """Check if user is admin"""
        return self.role == 'admin' or self.is_staff or self.is_superuser

    @property
    def is_teacher(self):
        """Check if user is teacher"""
        return self.role == 'teacher'

    @property
    def is_student(self):
        """Check if user is student"""
        return self.role == 'student'
