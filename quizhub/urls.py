
from django.contrib import admin
from django.urls import path, include
from django.contrib.sitemaps.views import sitemap
from .sitemaps import StaticViewSitemap, QuizSitemap, CategorySitemap

sitemaps = {
    'static': StaticViewSitemap,
    'quizzes': QuizSitemap,
    'categories': CategorySitemap,
}

urlpatterns = [
    path('admin/', admin.site.urls),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    # Landing page
    path('', include('core.urls', namespace='core')),
    # User authentication and dashboard
    path('users/', include('users.urls', namespace='users')),
    path('quiz/', include(('quizzes.urls', 'quizzes'), namespace='quizzes')),
    path('textprocessor/', include('textprocessor.urls')),
    path('ai/', include('ai.urls')),
    path('admin-dashboard/', include('admin_dashboard.urls', namespace='admin_dashboard')),

]
