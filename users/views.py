from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.db.models import Avg, Count, Max
from django.utils import timezone
from .models import CustomUser
from .decorators import role_required
from quizzes.models import Quiz, UserQuizAttempt


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


def user_login(request):
    # If the user is trying to access the admin panel, redirect to the default admin login
    next_url = request.GET.get('next', '')
    if next_url.startswith('/admin/'):
        return redirect('/admin/login/')

    if request.user.is_authenticated:
        # If user is already authenticated, redirect to the 'next' parameter or dashboard
        next_url = next_url or 'users:dashboard'
        return redirect(next_url)

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()

        if not all([username, password]):
            messages.error(request, "Username and password are required.")
            return redirect('users:login')

        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            # Set session expiry (e.g., 30 minutes of inactivity)
            request.session.set_expiry(1800)
            request.session['last_activity'] = str(request.session.get_expiry_date())
            messages.success(request, f"Welcome, {user.full_name}!")
            # Redirect to the 'next' parameter or dashboard
            next_url = next_url or 'users:dashboard'
            return redirect(next_url)
        else:
            messages.error(request, "Invalid credentials.")
            # Preserve 'next' parameter in case of login failure
            if next_url:
                return redirect(f"{reverse('users:login')}?next={next_url}")
            return redirect('users:login')

    return render(request, 'users/login.html')


def user_logout(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect('users:login')


@login_required
def dashboard(request):
    """
    Unified dashboard view that renders role-specific templates.
    """
    user = request.user
    template_map = {
        'student': 'base/student_base.html',
        'teacher': 'base/dashboard_base.html',
        'admin': 'admin/dash_admin.html'
    }
    template = template_map.get(user.role)
    if not template:
        messages.error(request, "Unknown user role. Contact admin.")
        return redirect('users:login')

    # Prepare dashboard context data
    context = {
        'dashboard_template': get_dashboard_template(user),
        'current_date': timezone.now(),
    }
    
    # Add student-specific context
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

    messages.success(request, f"You are logged in as a {user.role}.")
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
            question_count=Count('questions')
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

def get_dashboard_template(user):
    """Helper function to determine the correct dashboard template based on user role"""
    if user.role == 'student':
        return 'student_dashboard.html'
    elif user.role == 'teacher':
        return 'teacher_dashboard.html'
    else:
        return 'admin_dashboard.html'