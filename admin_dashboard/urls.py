from django.urls import path
from . import views

app_name = 'admin_dashboard'

urlpatterns = [
    # Main admin dashboard
    path('', views.admin_dashboard, name='dashboard'),
    
    # User management
    path('users/', views.manage_users, name='manage_users'),
    path('users/toggle-status/', views.toggle_user_status, name='toggle_user_status'),
    
    # Quiz management
    path('quizzes/', views.manage_quizzes, name='manage_quizzes'),
    path('quizzes/toggle-status/', views.toggle_quiz_status, name='toggle_quiz_status'),
    
    # AI prompt management
    path('ai-prompts/', views.manage_ai_prompts, name='manage_ai_prompts'),
    
    # System settings
    path('settings/', views.system_settings, name='system_settings'),
    
    # API endpoints
    path('api/analytics/', views.admin_analytics_api, name='admin_analytics_api'),
]
