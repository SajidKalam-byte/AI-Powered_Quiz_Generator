from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Count, Avg, Q
from django.http import JsonResponse
from django.utils import timezone
from django.core.paginator import Paginator
from datetime import timedelta
import json

from .models import (
    Quiz, Question, Category, UserQuizAttempt, 
    UserProfile, DailyChallenge, Leaderboard
)
from .forms import QuizForm, QuestionForm, AIGenerateQuizForm
from .analytics import AnalyticsService

def get_dashboard_template(user):
    """Returns the correct base dashboard layout template based on user role."""
    # Use the same modern template for all users to ensure consistent UI
    return 'base/student_base.html'

def get_or_create_user_profile(user):
    """Get or create user profile for points tracking"""
    profile, created = UserProfile.objects.get_or_create(user=user)
    return profile

# ==================== QUIZ LIST AND BROWSE ====================

def quiz_list(request):
    """Enhanced quiz list with filtering, search, and pagination"""
    quizzes_query = Quiz.objects.filter(is_published=True).select_related('category')
    
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
    
    # Filter by difficulty
    difficulty_filter = request.GET.get('difficulty', '')
    if difficulty_filter:
        quizzes_query = quizzes_query.filter(difficulty=difficulty_filter)
    
    # Filter by quiz type
    quiz_type_filter = request.GET.get('type', '')
    if quiz_type_filter:
        quizzes_query = quizzes_query.filter(quiz_type=quiz_type_filter)
    
    # Sorting
    sort_by = request.GET.get('sort', '-created_at')
    valid_sorts = ['-created_at', 'title', '-total_attempts', '-average_score', 'difficulty']
    if sort_by in valid_sorts:
        quizzes_query = quizzes_query.order_by(sort_by)
    
    # Pagination
    paginator = Paginator(quizzes_query, 12)  # Show 12 quizzes per page
    page_number = request.GET.get('page')
    quizzes = paginator.get_page(page_number)
    
    # Get categories for filter dropdown
    categories = Category.objects.filter(is_active=True)
    
    # Get daily challenge
    daily_challenge = DailyChallenge.get_today_challenge()
    
    context = {
        'quizzes': quizzes,
        'categories': categories,
        'search_query': search_query,
        'category_filter': category_filter,
        'difficulty_filter': difficulty_filter,
        'quiz_type_filter': quiz_type_filter,
        'sort_by': sort_by,
        'daily_challenge': daily_challenge,
        'dashboard_template': get_dashboard_template(request.user) if request.user.is_authenticated else 'base/auth_base.html'
    }
    
    return render(request, 'quizzes/quiz_list.html', context)

def quiz_detail(request, quiz_id):
    """Enhanced quiz detail view with attempt history and stats"""
    quiz = get_object_or_404(
        Quiz.objects.select_related('category', 'created_by').prefetch_related('questions'),
        id=quiz_id,
        is_published=True
    )
    
    user_attempts = []
    can_attempt = True
    attempts_left = quiz.max_attempts
    
    if request.user.is_authenticated:
        user_attempts = UserQuizAttempt.objects.filter(
            user=request.user, 
            quiz=quiz,
            status='COMPLETED'
        ).order_by('-completed_at')[:5]
        
        attempts_left = quiz.max_attempts - user_attempts.count()
        can_attempt = attempts_left > 0
    
    # Pre-split tags for the template
    tag_list = quiz.tags.split(",") if quiz.tags else []

    context = {
        'quiz': quiz,
        'tag_list': tag_list,
        'user_attempts': user_attempts,
        'can_attempt': can_attempt,
        'attempts_left': attempts_left,
        'dashboard_template': get_dashboard_template(request.user) if request.user.is_authenticated else 'base/auth_base.html'
    }
    
    return render(request, 'quizzes/quiz_detail.html', context)


# ==================== QUIZ TAKING ====================

@login_required
def take_quiz(request, quiz_id):
    """Start or continue taking a quiz"""
    quiz = get_object_or_404(Quiz, id=quiz_id, is_published=True)
    
    # Check if user has attempts left
    completed_attempts = UserQuizAttempt.objects.filter(
        user=request.user,
        quiz=quiz,
        status='COMPLETED'
    ).count()
    
    if completed_attempts >= quiz.max_attempts:
        messages.error(request, f"You have reached the maximum number of attempts ({quiz.max_attempts}) for this quiz.")
        return redirect('quizzes:quiz_detail', quiz_id=quiz_id)
    
    # Check for existing in-progress attempt
    in_progress_attempt = UserQuizAttempt.objects.filter(
        user=request.user,
        quiz=quiz,
        status='IN_PROGRESS'
    ).first()
    
    if not in_progress_attempt:
        # Create new attempt
        in_progress_attempt = UserQuizAttempt.objects.create(
            user=request.user,
            quiz=quiz,
            status='IN_PROGRESS',
            max_possible_score=quiz.questions.count()
        )
    
    questions = quiz.questions.all().order_by('order')
    
    context = {
        'quiz': quiz,
        'questions': questions,
        'attempt': in_progress_attempt,
        'dashboard_template': get_dashboard_template(request.user)
    }
    
    return render(request, 'quizzes/take_quiz.html', context)

@login_required 
def submit_quiz(request, quiz_id):
    """Submit quiz answers and calculate score"""
    if request.method != 'POST':
        return redirect('quizzes:take_quiz', quiz_id=quiz_id)
    
    quiz = get_object_or_404(Quiz, id=quiz_id, is_published=True)
    
    # Get the in-progress attempt
    attempt = get_object_or_404(
        UserQuizAttempt,
        user=request.user,
        quiz=quiz,
        status='IN_PROGRESS'
    )
    
    # Process answers
    answers = {}
    for key, value in request.POST.items():
        if key.startswith('question_'):
            question_id = key.replace('question_', '')
            answers[question_id] = value
    
    # Calculate time taken
    time_taken = timezone.now() - attempt.started_at
    
    # Update attempt
    attempt.answers = answers
    attempt.time_taken = time_taken
    attempt.completed_at = timezone.now()
    attempt.status = 'COMPLETED'
    attempt.calculate_score()  # This method calculates score and percentage
    
    # Update user profile and add points
    profile = get_or_create_user_profile(request.user)
    profile.add_points(attempt.points_earned)
    profile.total_quizzes_completed += 1
    profile.update_streak()
    profile.save()
    
    # Update quiz statistics
    quiz.total_attempts += 1
    quiz.total_completions += 1
    quiz.save()
    
    messages.success(request, f"Quiz completed! You scored {attempt.score}/{attempt.max_possible_score} and earned {attempt.points_earned} points!")
    
    return redirect('quizzes:quiz_result', quiz_id=quiz_id, attempt_id=attempt.id)

@login_required
def quiz_result(request, quiz_id, attempt_id):
    """Show quiz results with detailed breakdown"""
    quiz = get_object_or_404(Quiz, id=quiz_id)
    attempt = get_object_or_404(UserQuizAttempt, id=attempt_id, user=request.user, quiz=quiz)
    
    # Get detailed results
    questions = quiz.questions.all().order_by('order')
    results = []
    answers = {}  # For template compatibility
    
    for question in questions:
        user_answer = attempt.answers.get(str(question.id), '')
        is_correct = user_answer == question.correct_option
        
        results.append({
            'question': question,
            'user_answer': user_answer,
            'is_correct': is_correct,
            'correct_answer': question.correct_option
        })
        
        # Store answers in the format expected by the template
        answers[question.id] = user_answer
    
    context = {
        'quiz': quiz,
        'attempt': attempt,
        'results': results,
        'questions': questions,
        'answers': answers,
        'score': attempt.score,
        'total': questions.count(),
        'dashboard_template': get_dashboard_template(request.user)
    }
    
    return render(request, 'quizzes/result.html', context)

# ==================== QUIZ CREATION ====================

@login_required
def quiz_create(request):
    """Create a new quiz"""
    if request.method == 'POST':
        form = QuizForm(request.POST)
        if form.is_valid():
            quiz = form.save(commit=False)
            quiz.created_by = request.user
            quiz.save()
            messages.success(request, 'Quiz created successfully! Now add some questions.')
            return redirect('quizzes:add_question', quiz_id=quiz.id)
    else:
        form = QuizForm()
    
    context = {
        'form': form,
        'dashboard_template': get_dashboard_template(request.user)
    }
    
    return render(request, 'quizzes/quiz_create.html', context)

@login_required
def add_question(request, quiz_id):
    """Add questions to a quiz"""
    quiz = get_object_or_404(Quiz, id=quiz_id, created_by=request.user)
    
    if request.method == 'POST':
        form = QuestionForm(request.POST)
        if form.is_valid():
            question = form.save(commit=False)
            question.quiz = quiz
            # Auto-assign order if not provided
            if not question.order:
                last_question = quiz.questions.order_by('-order').first()
                question.order = (last_question.order + 1) if last_question else 1
            question.save()
            messages.success(request, 'Question added successfully!')
            return redirect('quizzes:add_question', quiz_id=quiz_id)
    else:
        form = QuestionForm()
    
    questions = quiz.questions.all().order_by('order')
    
    context = {
        'quiz': quiz,
        'form': form,
        'questions': questions,
        'dashboard_template': get_dashboard_template(request.user)
    }
    
    return render(request, 'quizzes/add_question.html', context)

# ==================== LEADERBOARD ====================

def leaderboard(request):
    """Display leaderboards for different periods"""
    period = request.GET.get('period', 'ALL_TIME')
    valid_periods = ['DAILY', 'WEEKLY', 'MONTHLY', 'ALL_TIME']
    
    if period not in valid_periods:
        period = 'ALL_TIME'
    
    # Update leaderboard data
    leaderboard_data = Leaderboard.update_leaderboard(period)
    
    context = {
        'leaderboard': leaderboard_data,
        'current_period': period,
        'valid_periods': valid_periods,
        'dashboard_template': get_dashboard_template(request.user) if request.user.is_authenticated else 'base/auth_base.html'
    }
    
    return render(request, 'quizzes/leaderboard.html', context)

# ==================== DAILY CHALLENGE ====================

def daily_challenge(request):
    """Display today's daily challenge"""
    challenge = DailyChallenge.get_today_challenge()
    
    if not challenge or not challenge.quiz:
        context = {
            'no_challenge': True,
            'dashboard_template': get_dashboard_template(request.user) if request.user.is_authenticated else 'base/auth_base.html'
        }
        return render(request, 'quizzes/daily_challenge.html', context)
    
    user_attempted = False
    if request.user.is_authenticated:
        user_attempted = UserQuizAttempt.objects.filter(
            user=request.user,
            quiz=challenge.quiz,
            status='COMPLETED',
            completed_at__date=timezone.now().date()
        ).exists()
    
    context = {
        'challenge': challenge,
        'user_attempted': user_attempted,
        'dashboard_template': get_dashboard_template(request.user) if request.user.is_authenticated else 'base/auth_base.html'
    }
    
    return render(request, 'quizzes/daily_challenge.html', context)

# ==================== AJAX ENDPOINTS ====================

@login_required
def save_quiz_progress(request):
    """AJAX endpoint to save quiz progress"""
    if request.method == 'POST':
        data = json.loads(request.body)
        attempt_id = data.get('attempt_id')
        answers = data.get('answers', {})
        
        try:
            attempt = UserQuizAttempt.objects.get(
                id=attempt_id,
                user=request.user,
                status='IN_PROGRESS'
            )
            attempt.answers = answers
            attempt.save()
            
            return JsonResponse({'success': True})
        except UserQuizAttempt.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Attempt not found'})
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})

def quiz_stats_api(request, quiz_id):
    """API endpoint for quiz statistics"""
    quiz = get_object_or_404(Quiz, id=quiz_id, is_published=True)
    
    stats = {
        'total_attempts': quiz.total_attempts,
        'total_completions': quiz.total_completions,
        'completion_rate': quiz.completion_rate,
        'average_score': quiz.average_score,
        'question_count': quiz.question_count,
        'difficulty': quiz.difficulty,
        'time_limit': quiz.time_limit
    }
    
    return JsonResponse(stats)

# ==================== ANALYTICS VIEWS ====================

@login_required
def analytics_dashboard(request):
    """Main analytics dashboard with comprehensive stats"""
    # Check if user has permission to view analytics
    if not request.user.is_staff and request.user.role not in ['teacher', 'admin']:
        messages.error(request, 'You do not have permission to view analytics.')
        return redirect('quizzes:quiz_list')
    
    analytics_service = AnalyticsService()
    
    # Get analytics based on user role
    if request.user.role == 'admin' or request.user.is_staff:
        # Platform-wide analytics for admins
        platform_data = analytics_service.get_platform_analytics()
        
        context = {
            'total_users': platform_data.total_users,
            'total_quizzes': platform_data.total_quizzes,
            'total_attempts': platform_data.total_quiz_attempts,
            'completion_rate': 85.0,  # Placeholder
            'popular_categories': platform_data.popular_categories,
            'recent_activity': [],  # Placeholder
            'user_engagement': platform_data.user_engagement_trends,
            'dashboard_template': get_dashboard_template(request.user)
        }
    else:
        # Teacher analytics - only their quizzes
        user_quizzes = Quiz.objects.filter(created_by=request.user)
        total_attempts = UserQuizAttempt.objects.filter(quiz__in=user_quizzes).count()
        avg_score = UserQuizAttempt.objects.filter(
            quiz__in=user_quizzes, 
            status='COMPLETED'
        ).aggregate(avg=Avg('score'))['avg'] or 0
        
        context = {
            'created_quizzes': {
                'total_quizzes': user_quizzes.count(),
                'total_attempts': total_attempts,
                'avg_score': avg_score
            },
            'student_performance': {'avg_score': avg_score, 'completion_rate': 80.0},
            'quiz_engagement': {'quiz_names': [], 'avg_scores': [], 'completion_rates': []},
            'dashboard_template': get_dashboard_template(request.user)
        }
    
    return render(request, 'quizzes/analytics_dashboard.html', context)

@login_required
def quiz_analytics(request, quiz_id):
    """Detailed analytics for a specific quiz"""
    quiz = get_object_or_404(Quiz, id=quiz_id)
    
    # Check permissions
    if not (request.user == quiz.created_by or request.user.is_staff or request.user.role == 'admin'):
        messages.error(request, 'You do not have permission to view this quiz\'s analytics.')
        return redirect('quizzes:quiz_detail', quiz_id=quiz_id)
    
    analytics_service = AnalyticsService()
    quiz_analytics = analytics_service.get_quiz_analytics(quiz, detailed=True)
    
    # Convert to dict for template
    performance_summary = {
        'total_attempts': quiz_analytics.total_attempts,
        'completed_attempts': quiz_analytics.total_attempts,  # Assuming all are completed
        'completion_rate': quiz_analytics.completion_rate,
        'average_score': quiz_analytics.average_score,
        'highest_score': 100.0,  # Placeholder
        'avg_time_taken': quiz_analytics.average_time / 60 if quiz_analytics.average_time else 0
    }
    
    context = {
        'quiz': quiz,
        'performance_summary': performance_summary,
        'question_analysis': quiz_analytics.question_analytics,
        'time_analysis': {'avg_time': quiz_analytics.average_time / 60, 'fastest_time': 5, 'slowest_time': 30, 'fast_percentage': 60},
        'attempt_trends': {'labels': [], 'attempts': [], 'scores': []},
        'user_performance': [],
        'difficulty_analysis': {'difficulty_rating': quiz_analytics.difficulty_rating},
        'dashboard_template': get_dashboard_template(request.user)
    }
    
    return render(request, 'quizzes/quiz_analytics.html', context)

# ==================== ANALYTICS API ENDPOINTS ====================

@login_required
def quiz_analytics_api(request, quiz_id):
    """API endpoint for quiz analytics data"""
    quiz = get_object_or_404(Quiz, id=quiz_id)
    
    # Check permissions
    if not (request.user == quiz.created_by or request.user.is_staff or request.user.role == 'admin'):
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    analytics_service = AnalyticsService()
    analytics_type = request.GET.get('type', 'summary')
    
    if analytics_type == 'summary':
        quiz_analytics = analytics_service.get_quiz_analytics(quiz)
        data = {
            'total_attempts': quiz_analytics.total_attempts,
            'average_score': quiz_analytics.average_score,
            'completion_rate': quiz_analytics.completion_rate
        }
    else:
        data = {'error': 'Invalid analytics type'}
    
    return JsonResponse(data)

@login_required
def user_analytics_api(request):
    """API endpoint for user analytics data"""
    analytics_service = AnalyticsService()
    analytics_type = request.GET.get('type', 'summary')
    
    if analytics_type == 'summary':
        user_metrics = analytics_service.get_user_analytics(request.user)
        data = {
            'total_quizzes_taken': user_metrics.total_quizzes_taken,
            'average_score': user_metrics.average_score,
            'total_time_spent': user_metrics.total_time_spent
        }
    else:
        data = {'error': 'Invalid analytics type'}
    
    return JsonResponse(data)

@login_required
def platform_analytics_api(request):
    """API endpoint for platform-wide analytics (admin only)"""
    if not (request.user.is_staff or request.user.role == 'admin'):
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    analytics_service = AnalyticsService()
    analytics_type = request.GET.get('type', 'summary')
    
    if analytics_type == 'summary':
        platform_data = analytics_service.get_platform_analytics()
        data = {
            'total_users': platform_data.total_users,
            'total_quizzes': platform_data.total_quizzes,
            'total_attempts': platform_data.total_quiz_attempts
        }
    else:
        data = {'error': 'Invalid analytics type'}
    
    return JsonResponse(data)
