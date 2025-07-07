from django.urls import path
from . import views

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
    
    # Special features
    path('leaderboard/', views.leaderboard, name='leaderboard'),
    path('daily-challenge/', views.daily_challenge, name='daily_challenge'),
    
    # AJAX endpoints
    path('save-progress/', views.save_quiz_progress, name='save_progress'),
    path('<uuid:quiz_id>/stats/', views.quiz_stats_api, name='quiz_stats_api'),
]