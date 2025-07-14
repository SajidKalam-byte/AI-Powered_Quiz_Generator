from django.urls import path
from django.shortcuts import redirect
from . import views

app_name = 'users'

urlpatterns = [
    # Authentication: login at /users/login/
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    # Dashboard moved to /users/dashboard/
    path('dashboard/', views.dashboard, name='dashboard'),
    # Registration
    path('student/register/', views.student_register, name='student_register'),
    path('teacher/register/', views.teacher_register, name='teacher_register'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/password/change/', views.change_password, name='password_change'),
]
