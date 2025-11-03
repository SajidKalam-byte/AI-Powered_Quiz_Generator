from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from quizzes.models import Quiz, Category
from django.contrib.auth import get_user_model

User = get_user_model()

class StaticViewSitemap(Sitemap):
    priority = 0.8
    changefreq = 'daily'
    protocol = 'https'

    def items(self):
        return ['core:home', 'users:login', 'users:student_register', 'users:teacher_register']

    def location(self, item):
        return reverse(item)

class QuizSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.7
    protocol = 'https'

    def items(self):
        return Quiz.objects.filter(is_published=True)

    def lastmod(self, obj):
        return obj.updated_at if hasattr(obj, 'updated_at') else obj.created_at

    def location(self, obj):
        return reverse('quizzes:quiz_detail', args=[obj.id])

class CategorySitemap(Sitemap):
    changefreq = 'monthly'
    priority = 0.6
    protocol = 'https'

    def items(self):
        return Category.objects.filter(is_active=True)

    def location(self, obj):
        return reverse('quizzes:quiz_list') + f'?category={obj.slug}'
