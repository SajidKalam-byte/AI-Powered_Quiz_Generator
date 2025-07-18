
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    # Landing page
    path('', include('core.urls', namespace='core')),
    # User authentication and dashboard
    path('users/', include('users.urls', namespace='users')),
    path('core/', include('core.urls')),
    path('quiz/', include(('quizzes.urls', 'quizzes'), namespace='quizzes')),
    path('textprocessor/', include('textprocessor.urls')),
    path('ai/', include('ai.urls')),
    path('admin-dashboard/', include('admin_dashboard.urls', namespace='admin_dashboard')),

]
