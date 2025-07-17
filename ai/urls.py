from django.urls import path
from . import views

app_name = 'ai'

urlpatterns = [
    path('test/', views.ai_test, name='test'),
    path('generate-quiz/', views.generate_quiz, name='generate_quiz'),
    path('generate-questions/', views.generate_quiz_questions, name='generate_questions'),
    path('discussion/', views.discussion, name='discussion'),
    path('chat/message/', views.chat_message, name='chat_message'),
    path('chat/history/', views.get_chat_history, name='chat_history'),
    path('chat/clear/', views.clear_chat_history, name='clear_chat_history'),
]
