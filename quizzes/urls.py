from django.urls import path, include
from . import views
from . import export_views

app_name = 'quizzes'

urlpatterns = [
    # Quiz browsing and listing
    path('', views.quiz_list, name='quiz_list'),
    path('<uuid:quiz_id>/', views.quiz_detail, name='quiz_detail'),
    
    # Quiz taking
    path('<uuid:quiz_id>/take/', views.take_quiz, name='take_quiz'),
    path('<uuid:quiz_id>/submit/', views.submit_quiz, name='submit_quiz'),
    path('<uuid:quiz_id>/result/<uuid:attempt_id>/', views.quiz_result, name='quiz_result'),
    
    # Quiz creation
    path('create/', views.quiz_create, name='quiz_create'),
    path('<uuid:quiz_id>/add-question/', views.add_question, name='add_question'),
    
    # Export features
    path('<uuid:quiz_id>/export/', export_views.export_quiz_form, name='quiz_export_form'),
    path('<uuid:quiz_id>/export/download/<str:format>/', export_views.export_quiz, name='quiz_export_download'),
    path('<uuid:quiz_id>/export/preview/<str:format>/', export_views.preview_quiz_export, name='quiz_export_preview'),
    path('export/history/', export_views.export_history, name='export_history'),
    
    # Analytics features
    path('analytics/', views.analytics_dashboard, name='analytics_dashboard'),
    path('<uuid:quiz_id>/analytics/', views.quiz_analytics, name='quiz_analytics'),
    path('analytics/api/quiz/<uuid:quiz_id>/', views.quiz_analytics_api, name='quiz_analytics_api'),
    path('analytics/api/user/', views.user_analytics_api, name='user_analytics_api'),
    path('analytics/api/platform/', views.platform_analytics_api, name='platform_analytics_api'),
    
    # Special features
    path('leaderboard/', views.leaderboard, name='leaderboard'),
    path('daily-challenge/', views.daily_challenge, name='daily_challenge'),
    
    # AJAX endpoints
    path('save-progress/', views.save_quiz_progress, name='save_progress'),
    path('<uuid:quiz_id>/stats/', views.quiz_stats_api, name='quiz_stats_api'),
]