from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from .models import CustomUser
from .decorators import role_required


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
        'admin': 'dashboard/admin_dash.html'
    }
    template = template_map.get(user.role)
    if not template:
        messages.error(request, "Unknown user role. Contact admin.")
        return redirect('users:login')

    messages.success(request, f"You are logged in as a {user.role}.")
    return render(request, template, {'dashboard_template': template})