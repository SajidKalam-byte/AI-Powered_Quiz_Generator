from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.contrib import messages
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.urls import reverse
from django.db.models import Avg, Count, Max
from django.utils import timezone
from django.conf import settings
import logging
from .models import CustomUser
from .decorators import role_required
from quizzes.models import Quiz, UserQuizAttempt
from django.http import JsonResponse

logger = logging.getLogger(__name__)


def _redirect_authenticated_user(request, user, next_url=''):
    """Helper function to redirect authenticated users to appropriate dashboard"""
    if not user.is_authenticated:
        messages.error(request, "User not authenticated.")
        return redirect('users:login')

    # Handle Django admin access
    if next_url.startswith('/admin/'):
        if user.is_staff or user.is_superuser or (hasattr(user, 'role') and user.role == 'admin'):
            return redirect(next_url)
        messages.error(request, "You don't have permission to access the admin panel.")
        return redirect('users:dashboard')

    # Handle admin dashboard access
    if next_url.startswith('/admin-dashboard/'):
        if (hasattr(user, 'role') and user.role == 'admin') or user.is_staff or user.is_superuser:
            return redirect(next_url)
        messages.error(request, "You don't have permission to access the admin dashboard.")
        return redirect('users:dashboard')

    # If there's a specific next URL and it's not restricted, use it
    if next_url and not next_url.startswith('/admin'):
        return redirect(next_url)

    # Default role-based redirection
    if hasattr(user, 'role'):
        if user.role == 'admin' or user.is_staff or user.is_superuser:
            try:
                return redirect('admin_dashboard:dashboard')
            except Exception as e:
                messages.error(request, f"Error redirecting to admin dashboard: {str(e)}")
                return redirect('users:dashboard')
        elif user.role == 'teacher':
            return redirect('users:dashboard')
        elif user.role == 'student':
            return redirect('users:dashboard')
        else:
            messages.error(request, f"Unknown user role: {user.role}")
            return redirect('users:login')
    else:
        # Fallback for users without role attribute
        if user.is_staff or user.is_superuser:
            try:
                return redirect('admin_dashboard:dashboard')
            except Exception as e:
                messages.error(request, f"Error redirecting to admin dashboard: {str(e)}")
                return redirect('users:dashboard')
        else:
            return redirect('users:dashboard')


def student_register(request):
    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        student_roll_no = request.POST.get('student_roll_no', '').strip()
        student_mail = request.POST.get('student_mail', '').strip()
        academic_year = request.POST.get('academic_year', '').strip()
        password = request.POST.get('password', '').strip()

        if not all([full_name, student_roll_no, student_mail, academic_year, password]):
            messages.error(request, "All fields are required.")
            return redirect('users:student_register')

        if CustomUser.objects.filter(username=student_roll_no).exists():
            messages.error(request, "Roll number already exists.")
            return redirect('users:student_register')

        if CustomUser.objects.filter(email=student_mail).exists():
            messages.error(request, "Email already exists.")
            return redirect('users:student_register')

        try:
            user = CustomUser.objects.create_user(
                username=student_roll_no,
                full_name=full_name,
                student_roll_no=student_roll_no,
                email=student_mail,
                academic_year=academic_year,
                role='student',
                password=password
            )
            messages.success(request, "Student registered successfully. Please login.")
            return redirect('users:login')
        except Exception as e:
            messages.error(request, f"Registration failed: {str(e)}")
            return redirect('users:student_register')

    return render(request, 'users/student_register.html')


def teacher_register(request):
    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        teacher_email = request.POST.get('teacher_email', '').strip()
        password = request.POST.get('password', '').strip()

        if not all([full_name, teacher_email, password]):
            messages.error(request, "All fields are required.")
            return redirect('users:teacher_register')

        if CustomUser.objects.filter(username=teacher_email).exists():
            messages.error(request, "Email already exists.")
            return redirect('users:teacher_register')

        try:
            user = CustomUser.objects.create_user(
                username=teacher_email,
                full_name=full_name,
                teacher_email=teacher_email,
                email=teacher_email,
                role='teacher',
                password=password
            )
            messages.success(request, "Teacher registered successfully. Please login.")
            return redirect('users:login')
        except Exception as e:
            messages.error(request, f"Registration failed: {str(e)}")
            return redirect('users:teacher_register')

    return render(request, 'users/teacher_register.html')


@never_cache
def user_login(request):
    # Redirect authenticated users to their dashboard
    if request.user.is_authenticated:
        return _redirect_authenticated_user(request, request.user, '')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()

        logger.info(f"Login attempt for username: {username}")

        if not all([username, password]):
            messages.error(request, "Username and password are required.")
            return redirect('users:login')

        try:
            # Add timing for authentication
            import time
            start_time = time.time()
            
            user = authenticate(request, username=username, password=password)
            auth_time = time.time() - start_time
            
            logger.info(f"Authentication took {auth_time:.2f} seconds")
            
            if user:
                login(request, user)
                request.session.set_expiry(3600)  # 1 hour
                logger.info(f"Login successful for user: {user.username}")
                messages.success(request, f"Welcome back, {user.full_name or user.username}!")
                return _redirect_authenticated_user(request, user, '')
            else:
                logger.warning(f"Authentication failed for username: {username}")
                messages.error(request, "Invalid username or password.")
                return redirect('users:login')
        except Exception as e:
            logger.error(f"Login error for username {username}: {str(e)}")
            messages.error(request, f"Login error: {str(e)}")
            return redirect('users:login')

    # Render login template
    return render(request, 'users/login.html')

def user_logout(request):
    from django.contrib.auth import logout
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect('core:home')

def dashboard(request):
    """
    Unified dashboard view that renders role-specific dashboard templates.
    """
    # Redirect unauthenticated users to login without next param
    if not request.user.is_authenticated:
        return redirect('users:login')
    user = request.user
    
    # For admin users, redirect to admin dashboard
    if user.role == 'admin' or user.is_staff or user.is_superuser:
        return redirect('admin_dashboard:dashboard')
    
    # Template mapping for non-admin users
    template_map = {
        'student': 'student/dashboard.html',
        'teacher': 'staff/dashboard.html',
    }
    
    template = template_map.get(user.role)
    if not template:
        messages.error(request, "Unknown user role. Contact admin.")
        return redirect('users:login')

    # Prepare dashboard context data
    context = {
        'current_date': timezone.now(),
    }
    
    # Add role-specific context
    if user.role == 'student':
        from textprocessor.models import UploadedFile
        from quizzes.models import Quiz
        
        # Get user's uploaded files
        user_files = UploadedFile.objects.filter(user=user)
        recent_files = user_files.order_by('-uploaded_at')[:5]
        
        # Calculate statistics
        uploaded_files_count = user_files.count()
        ai_generated_quizzes = Quiz.objects.filter(created_by=user).count()
        
        # Add to context
        context.update({
            'recent_files': recent_files,
            'uploaded_files_count': uploaded_files_count,
            'ai_generated_quizzes': ai_generated_quizzes,
            'quizzes_completed': 0,  # TODO: Implement quiz attempts tracking
            'average_score': 85,     # TODO: Calculate from quiz results
        })
    
    elif user.role == 'teacher':
        from textprocessor.models import UploadedFile
        from quizzes.models import Quiz
        
        # Get teacher's uploaded files
        user_files = UploadedFile.objects.filter(user=user)
        recent_files = user_files.order_by('-uploaded_at')[:5]
        
        # Calculate statistics
        uploaded_files_count = user_files.count()
        ai_generated_quizzes = Quiz.objects.filter(created_by=user).count()
        
        # Add to context
        context.update({
            'recent_files': recent_files,
            'uploaded_files_count': uploaded_files_count,
            'ai_generated_quizzes': ai_generated_quizzes,
            'total_students': 0,  # TODO: Implement student tracking
            'active_quizzes': ai_generated_quizzes,
        })

    messages.success(request, f"Welcome to your {user.role} dashboard!")
    return render(request, template, context)

@login_required
def profile_view(request):
    user = request.user
    
    # Calculate basic quiz statistics
    created_quizzes_count = Quiz.objects.filter(created_by=user).count()
    quiz_attempts = UserQuizAttempt.objects.filter(user=user).select_related('quiz', 'quiz__category').order_by('-completed_at')[:10]
    attempted_quizzes_count = UserQuizAttempt.objects.filter(user=user).values('quiz').distinct().count()
    
    # Calculate average score (excluding quizzes with no score)
    average_score = UserQuizAttempt.objects.filter(user=user).aggregate(
        avg_score=Avg('score')
    )['avg_score']
    
    # Get last attempt date if available
    last_attempt = UserQuizAttempt.objects.filter(user=user).aggregate(
        last_attempt=Max('completed_at')
    )
    last_attempt_date = last_attempt['last_attempt'].strftime("%B %d, %Y") if last_attempt['last_attempt'] else None
    
    # Get created quizzes for teachers/admins
    created_quizzes = []
    if user.role in ['teacher', 'admin']:
        created_quizzes = Quiz.objects.filter(created_by=user).select_related('category').annotate(
            num_questions=Count('questions')
        ).order_by('-created_at')[:10]
    
    context = {
        'dashboard_template': get_dashboard_template(user),
        'created_quizzes_count': created_quizzes_count,
        'attempted_quizzes_count': attempted_quizzes_count,
        'average_score': round(average_score, 1) if average_score else None,
        'last_attempt_date': last_attempt_date,
        'quiz_attempts': quiz_attempts,
        'created_quizzes': created_quizzes,
    }
    
    return render(request, 'base/profile.html', context)
@login_required
def edit_profile(request):
    from .forms import ProfileForm
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('users:profile')
    else:
        form = ProfileForm(instance=request.user)
    return render(request, 'users/edit_profile.html', {
        'form': form,
        'dashboard_template': get_dashboard_template(request.user)
    })

@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Password changed successfully.')
            return redirect('users:profile')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'users/change_password.html', {
        'form': form,
        'dashboard_template': get_dashboard_template(request.user)
    })

def get_dashboard_template(user):
    """Helper function to determine the correct base template based on user role"""
    # Use the same modern template for all users to ensure consistent UI
    return 'base/student_base.html'