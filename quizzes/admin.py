from django.contrib import admin
from .models import Category, Quiz, Question, UserQuizAttempt

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'description')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'created_by', 'created_at', 'is_published', 'difficulty')
    list_filter = ('category', 'is_published', 'difficulty')
    search_fields = ('title', 'created_by__username')
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'created_at'
    list_editable = ('is_published',)

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'quiz', 'correct_option', 'order')
    list_filter = ('quiz__title',)
    search_fields = ('text', 'quiz__title')
    list_editable = ('order',)

@admin.register(UserQuizAttempt)
class UserQuizAttemptAdmin(admin.ModelAdmin):
    list_display = ('user', 'quiz', 'score', 'completed_at')
    list_filter = ('quiz', 'completed_at')
    search_fields = ('user__username', 'quiz__title')
    date_hierarchy = 'completed_at'