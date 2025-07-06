from django.urls import path
from . import views

app_name = 'textprocessor'

urlpatterns = [
    # File upload and management
    path('', views.file_list, name='file_list'),
    path('upload/', views.upload_file, name='upload'),
    path('files/', views.file_list, name='file_list'),
    path('files/<int:file_id>/', views.file_detail, name='file_detail'),
    path('files/<int:file_id>/delete/', views.delete_file, name='delete_file'),
    path('files/<int:file_id>/reprocess/', views.reprocess_file, name='reprocess_file'),
    
    # Quiz generation from files
    path('generate-quiz/', views.generate_quiz_from_file, name='generate_quiz'),
    
    # Legacy compatibility
    path('upload-view/', views.upload_file_view, name='upload_view'),
]