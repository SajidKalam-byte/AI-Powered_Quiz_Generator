from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count, Q, Avg
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
import json

from users.models import CustomUser
from quizzes.models import Quiz, UserQuizAttempt, Category
from quizzes.analytics import PlatformAnalytics
from ai.models import AIPromptTemplate, AIUsageLog


def is_admin_or_staff(user):
    """Check if user is admin or staff"""
    return user.is_staff or (hasattr(user, 'role') and user.role == 'admin')


@login_required
@user_passes_test(is_admin_or_staff)
def admin_dashboard(request):
    """Main admin dashboard with comprehensive platform statistics"""
    
    # Platform analytics
    platform_analytics = PlatformAnalytics()
    
    # Key metrics
    total_users = platform_analytics.get_total_users()
    total_quizzes = platform_analytics.get_total_quizzes()
    total_attempts = platform_analytics.get_total_quiz_attempts()
    completion_rate = platform_analytics.get_platform_completion_rate()
    
    # Recent activity
    recent_activity = platform_analytics.get_recent_activity()
    user_engagement = platform_analytics.get_user_engagement_metrics()
    popular_categories = platform_analytics.get_popular_categories()
    
    # Recent users
    recent_users = CustomUser.objects.filter(
        date_joined__gte=timezone.now() - timedelta(days=7)
    ).order_by('-date_joined')[:10]
    
    # Recent quizzes
    recent_quizzes = Quiz.objects.select_related('created_by', 'category').order_by('-created_at')[:10]
    
    # AI usage statistics
    ai_usage_today = AIUsageLog.objects.filter(
        timestamp__date=timezone.now().date()
    ).count() if hasattr(AIUsageLog, 'objects') else 0
    
    # System health metrics
    inactive_users = CustomUser.objects.filter(
        last_login__lt=timezone.now() - timedelta(days=30),
        is_active=True
    ).count()
    
    context = {
        'total_users': total_users,
        'total_quizzes': total_quizzes,
        'total_attempts': total_attempts,
        'completion_rate': completion_rate,
        'recent_activity': recent_activity,
        'user_engagement': user_engagement,
        'popular_categories': popular_categories,
        'recent_users': recent_users,
        'recent_quizzes': recent_quizzes,
        'ai_usage_today': ai_usage_today,
        'inactive_users': inactive_users,
    }
    
    return render(request, 'admin_dashboard/dashboard.html', context)


@login_required
@user_passes_test(is_admin_or_staff)
def manage_users(request):
    """User management interface"""
    
    users_query = CustomUser.objects.all()
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        users_query = users_query.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(full_name__icontains=search_query)
        )
    
    # Filter by role
    role_filter = request.GET.get('role', '')
    if role_filter:
        users_query = users_query.filter(role=role_filter)
    
    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter == 'active':
        users_query = users_query.filter(is_active=True)
    elif status_filter == 'inactive':
        users_query = users_query.filter(is_active=False)
    
    # Sorting
    sort_by = request.GET.get('sort', '-date_joined')
    valid_sorts = ['-date_joined', 'username', 'email', 'role', '-last_login']
    if sort_by in valid_sorts:
        users_query = users_query.order_by(sort_by)
    
    # Pagination
    paginator = Paginator(users_query, 25)
    page_number = request.GET.get('page')
    users = paginator.get_page(page_number)
    
    # User statistics
    user_stats = {
        'total_users': CustomUser.objects.count(),
        'active_users': CustomUser.objects.filter(is_active=True).count(),
        'students': CustomUser.objects.filter(role='student').count(),
        'teachers': CustomUser.objects.filter(role='teacher').count(),
        'recent_signups': CustomUser.objects.filter(
            date_joined__gte=timezone.now() - timedelta(days=7)
        ).count(),
    }
    
    context = {
        'users': users,
        'user_stats': user_stats,
        'search_query': search_query,
        'role_filter': role_filter,
        'status_filter': status_filter,
        'sort_by': sort_by,
    }
    
    return render(request, 'admin_dashboard/manage_users.html', context)


@login_required
@user_passes_test(is_admin_or_staff)
def manage_quizzes(request):
    """Quiz management interface"""
    
    quizzes_query = Quiz.objects.select_related('created_by', 'category')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        quizzes_query = quizzes_query.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(tags__icontains=search_query)
        )
    
    # Filter by category
    category_filter = request.GET.get('category', '')
    if category_filter:
        quizzes_query = quizzes_query.filter(category__slug=category_filter)
    
    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter == 'published':
        quizzes_query = quizzes_query.filter(is_published=True)
    elif status_filter == 'unpublished':
        quizzes_query = quizzes_query.filter(is_published=False)
    
    # Filter by difficulty
    difficulty_filter = request.GET.get('difficulty', '')
    if difficulty_filter:
        quizzes_query = quizzes_query.filter(difficulty=difficulty_filter)
    
    # Sorting
    sort_by = request.GET.get('sort', '-created_at')
    valid_sorts = ['-created_at', 'title', '-total_attempts', '-average_score']
    if sort_by in valid_sorts:
        quizzes_query = quizzes_query.order_by(sort_by)
    
    # Pagination
    paginator = Paginator(quizzes_query, 25)
    page_number = request.GET.get('page')
    quizzes = paginator.get_page(page_number)
    
    # Quiz statistics
    quiz_stats = {
        'total_quizzes': Quiz.objects.count(),
        'published_quizzes': Quiz.objects.filter(is_published=True).count(),
        'total_attempts': UserQuizAttempt.objects.count(),
        'completed_attempts': UserQuizAttempt.objects.filter(status='COMPLETED').count(),
        'categories': Category.objects.filter(is_active=True),
    }
    
    context = {
        'quizzes': quizzes,
        'quiz_stats': quiz_stats,
        'search_query': search_query,
        'category_filter': category_filter,
        'status_filter': status_filter,
        'difficulty_filter': difficulty_filter,
        'sort_by': sort_by,
    }
    
    return render(request, 'admin_dashboard/manage_quizzes.html', context)


@login_required
@user_passes_test(is_admin_or_staff)
def manage_ai_prompts(request):
    """AI prompt template management"""
    
    # Get or create AI prompt templates if they don't exist
    try:
        prompts = AIPromptTemplate.objects.all()
    except:
        prompts = []
    
    if request.method == 'POST':
        # Handle prompt creation/update
        action = request.POST.get('action')
        
        if action == 'create':
            name = request.POST.get('name')
            template = request.POST.get('template')
            description = request.POST.get('description')
            
            try:
                AIPromptTemplate.objects.create(
                    name=name,
                    template=template,
                    description=description,
                    created_by=request.user
                )
                messages.success(request, 'AI prompt template created successfully.')
            except Exception as e:
                messages.error(request, f'Error creating prompt template: {str(e)}')
        
        elif action == 'update':
            prompt_id = request.POST.get('prompt_id')
            try:
                prompt = AIPromptTemplate.objects.get(id=prompt_id)
                prompt.name = request.POST.get('name')
                prompt.template = request.POST.get('template')
                prompt.description = request.POST.get('description')
                prompt.save()
                messages.success(request, 'AI prompt template updated successfully.')
            except AIPromptTemplate.DoesNotExist:
                messages.error(request, 'Prompt template not found.')
            except Exception as e:
                messages.error(request, f'Error updating prompt template: {str(e)}')
        
        elif action == 'delete':
            prompt_id = request.POST.get('prompt_id')
            try:
                prompt = AIPromptTemplate.objects.get(id=prompt_id)
                prompt.delete()
                messages.success(request, 'AI prompt template deleted successfully.')
            except AIPromptTemplate.DoesNotExist:
                messages.error(request, 'Prompt template not found.')
            except Exception as e:
                messages.error(request, f'Error deleting prompt template: {str(e)}')
        
        return redirect('admin_dashboard:manage_ai_prompts')
    
    # AI usage statistics
    try:
        ai_stats = {
            'total_prompts': AIPromptTemplate.objects.count() if hasattr(AIPromptTemplate, 'objects') else 0,
            'usage_today': AIUsageLog.objects.filter(
                timestamp__date=timezone.now().date()
            ).count() if hasattr(AIUsageLog, 'objects') else 0,
            'usage_week': AIUsageLog.objects.filter(
                timestamp__gte=timezone.now() - timedelta(days=7)
            ).count() if hasattr(AIUsageLog, 'objects') else 0,
        }
    except:
        ai_stats = {
            'total_prompts': 0,
            'usage_today': 0,
            'usage_week': 0,
        }
    
    context = {
        'prompts': prompts,
        'ai_stats': ai_stats,
    }
    
    return render(request, 'admin_dashboard/manage_ai_prompts.html', context)


@login_required
@user_passes_test(is_admin_or_staff)
def system_settings(request):
    """System settings management"""
    
    if request.method == 'POST':
        # Handle settings updates
        setting_type = request.POST.get('setting_type')
        
        if setting_type == 'ai_settings':
            # Update AI settings (you can implement this based on your needs)
            messages.success(request, 'AI settings updated successfully.')
        
        elif setting_type == 'quiz_settings':
            # Update quiz settings
            messages.success(request, 'Quiz settings updated successfully.')
        
        elif setting_type == 'user_settings':
            # Update user settings
            messages.success(request, 'User settings updated successfully.')
        
        return redirect('admin_dashboard:system_settings')
    
    # Current settings (implement based on your settings model)
    settings = {
        'ai_enabled': True,
        'max_quiz_questions': 50,
        'default_time_limit': 60,
        'allow_guest_access': False,
        'auto_publish_quizzes': False,
    }
    
    context = {
        'settings': settings,
    }
    
    return render(request, 'admin_dashboard/system_settings.html', context)


# AJAX endpoints
@login_required
@user_passes_test(is_admin_or_staff)
def toggle_user_status(request):
    """AJAX endpoint to toggle user active status"""
    if request.method == 'POST':
        data = json.loads(request.body)
        user_id = data.get('user_id')
        
        try:
            user = CustomUser.objects.get(id=user_id)
            user.is_active = not user.is_active
            user.save()
            
            return JsonResponse({
                'success': True,
                'is_active': user.is_active,
                'message': f'User {"activated" if user.is_active else "deactivated"} successfully.'
            })
        except CustomUser.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'User not found'})
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})


@login_required
@user_passes_test(is_admin_or_staff)
def toggle_quiz_status(request):
    """AJAX endpoint to toggle quiz published status"""
    if request.method == 'POST':
        data = json.loads(request.body)
        quiz_id = data.get('quiz_id')
        
        try:
            quiz = Quiz.objects.get(id=quiz_id)
            quiz.is_published = not quiz.is_published
            quiz.save()
            
            return JsonResponse({
                'success': True,
                'is_published': quiz.is_published,
                'message': f'Quiz {"published" if quiz.is_published else "unpublished"} successfully.'
            })
        except Quiz.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Quiz not found'})
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})


@login_required
@user_passes_test(is_admin_or_staff)
def admin_analytics_api(request):
    """API endpoint for admin analytics data"""
    analytics_type = request.GET.get('type', 'summary')
    platform_analytics = PlatformAnalytics()
    
    if analytics_type == 'summary':
        data = {
            'total_users': platform_analytics.get_total_users(),
            'total_quizzes': platform_analytics.get_total_quizzes(),
            'total_attempts': platform_analytics.get_total_quiz_attempts(),
            'completion_rate': platform_analytics.get_platform_completion_rate()
        }
    elif analytics_type == 'users':
        data = platform_analytics.get_user_engagement_metrics()
    elif analytics_type == 'quizzes':
        data = platform_analytics.get_popular_categories()
    elif analytics_type == 'activity':
        data = platform_analytics.get_recent_activity()
    else:
        return JsonResponse({'error': 'Invalid analytics type'}, status=400)
    
    return JsonResponse(data)
