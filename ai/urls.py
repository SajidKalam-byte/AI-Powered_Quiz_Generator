from django.urls import path
from . import views

app_name = 'ai'

urlpatterns = [
    path('test/', views.ai_test, name='test'),
    path('generate-quiz/', views.generate_quiz, name='generate_quiz'),
    path('generate-questions/', views.generate_quiz_questions, name='generate_questions'),
]
