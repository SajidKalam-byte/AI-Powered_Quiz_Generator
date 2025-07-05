from django.urls import path
from . import views

app_name = 'textprocessor'

urlpatterns = [
    path('upload/', views.upload_file, name='upload'),
    path('upload-view/', views.upload_file_view, name='upload_view'),
]