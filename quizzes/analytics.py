"""
Advanced analytics and reporting system for quizzes
"""
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from collections import defaultdict

from django.db import models
from django.db.models import Avg, Count, Sum, Max, Min, Q, F
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.cache import cache

User = get_user_model()
logger = logging.getLogger(__name__)

@dataclass
class QuizPerformanceMetrics:
    """Quiz performance metrics"""
    total_attempts: int
    unique_users: int
    average_score: float
    median_score: float
    completion_rate: float
    average_time: int  # seconds
    difficulty_rating: float
    question_analytics: Dict[str, Any]

@dataclass
class UserPerformanceMetrics:
    """User performance metrics"""
    total_quizzes_taken: int
    average_score: float
    total_time_spent: int  # minutes
    favorite_categories: List[str]
    difficulty_preferences: Dict[str, int]
    learning_progress: Dict[str, Any]

@dataclass
class PlatformAnalytics:
    """Platform-wide analytics"""
    total_users: int
    active_users_last_30_days: int
    total_quizzes: int
    total_questions: int
    total_quiz_attempts: int
    popular_categories: List[Dict[str, Any]]
    user_engagement_trends: Dict[str, Any]

class AnalyticsService:
    """Comprehensive analytics service"""
    
    def __init__(self):
        self.cache_timeout = 3600  # 1 hour
    
    def get_quiz_analytics(self, quiz, detailed: bool = False) -> QuizPerformanceMetrics:
        """Get comprehensive analytics for a quiz"""
        cache_key = f"quiz_analytics_{quiz.id}_{detailed}"
        cached_result = cache.get(cache_key)
        
        if cached_result:
            return QuizPerformanceMetrics(**cached_result)
        
        try:
            from quizzes.models import UserQuizAttempt
            
            # Get all attempts for this quiz
            attempts = UserQuizAttempt.objects.filter(quiz=quiz, is_completed=True)
            
            if not attempts.exists():
                return QuizPerformanceMetrics(
                    total_attempts=0,
                    unique_users=0,
                    average_score=0,
                    median_score=0,
                    completion_rate=0,
                    average_time=0,
                    difficulty_rating=0,
                    question_analytics={}
                )
            
            # Basic metrics
            total_attempts = attempts.count()
            unique_users = attempts.values('user').distinct().count()
            
            # Score metrics
            scores = list(attempts.values_list('percentage', flat=True))
            average_score = sum(scores) / len(scores)
            median_score = sorted(scores)[len(scores) // 2]
            
            # Time metrics
            times = list(attempts.exclude(time_taken__isnull=True).values_list('time_taken', flat=True))
            average_time = sum(times) / len(times) if times else 0
            
            # Completion rate (completed vs started)
            all_attempts = UserQuizAttempt.objects.filter(quiz=quiz)
            completion_rate = (total_attempts / all_attempts.count() * 100) if all_attempts.exists() else 0
            
            # Question-level analytics
            question_analytics = {}
            if detailed:
                question_analytics = self._get_question_analytics(quiz, attempts)
            
            # Difficulty rating (based on average score and completion rate)
            difficulty_rating = self._calculate_difficulty_rating(average_score, completion_rate)
            
            result = QuizPerformanceMetrics(
                total_attempts=total_attempts,
                unique_users=unique_users,
                average_score=average_score,
                median_score=median_score,
                completion_rate=completion_rate,
                average_time=int(average_time),
                difficulty_rating=difficulty_rating,
                question_analytics=question_analytics
            )
            
            # Cache result
            cache.set(cache_key, result.__dict__, self.cache_timeout)
            return result
            
        except Exception as e:
            logger.error(f"Failed to get quiz analytics: {str(e)}")
            return QuizPerformanceMetrics(0, 0, 0, 0, 0, 0, 0, {})
    
    def get_user_analytics(self, user) -> UserPerformanceMetrics:
        """Get comprehensive analytics for a user"""
        cache_key = f"user_analytics_{user.id}"
        cached_result = cache.get(cache_key)
        
        if cached_result:
            return UserPerformanceMetrics(**cached_result)
        
        try:
            from quizzes.models import UserQuizAttempt, Quiz
            
            # Get user's quiz attempts
            attempts = UserQuizAttempt.objects.filter(
                user=user, 
                is_completed=True
            ).select_related('quiz', 'quiz__category')
            
            if not attempts.exists():
                return UserPerformanceMetrics(0, 0, 0, [], {}, {})
            
            total_quizzes = attempts.count()
            
            # Score metrics
            average_score = attempts.aggregate(avg_score=Avg('percentage'))['avg_score'] or 0
            
            # Time metrics
            total_time = attempts.exclude(time_taken__isnull=True).aggregate(
                total_time=Sum('time_taken')
            )['total_time'] or 0
            total_time_minutes = total_time // 60
            
            # Category analysis
            category_counts = defaultdict(int)
            for attempt in attempts:
                if attempt.quiz.category:
                    category_counts[attempt.quiz.category.name] += 1
            
            favorite_categories = sorted(
                category_counts.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:5]
            favorite_categories = [cat[0] for cat in favorite_categories]
            
            # Difficulty preferences
            difficulty_counts = defaultdict(int)
            for attempt in attempts:
                difficulty_counts[attempt.quiz.difficulty] += 1
            
            # Learning progress analysis
            learning_progress = self._analyze_learning_progress(attempts)
            
            result = UserPerformanceMetrics(
                total_quizzes_taken=total_quizzes,
                average_score=average_score,
                total_time_spent=total_time_minutes,
                favorite_categories=favorite_categories,
                difficulty_preferences=dict(difficulty_counts),
                learning_progress=learning_progress
            )
            
            # Cache result
            cache.set(cache_key, result.__dict__, self.cache_timeout)
            return result
            
        except Exception as e:
            logger.error(f"Failed to get user analytics: {str(e)}")
            return UserPerformanceMetrics(0, 0, 0, [], {}, {})
    
    def get_platform_analytics(self) -> PlatformAnalytics:
        """Get platform-wide analytics"""
        cache_key = "platform_analytics"
        cached_result = cache.get(cache_key)
        
        if cached_result:
            return PlatformAnalytics(**cached_result)
        
        try:
            from quizzes.models import Quiz, Question, UserQuizAttempt, Category
            
            # User metrics
            total_users = User.objects.count()
            
            # Active users (last 30 days)
            thirty_days_ago = timezone.now() - timedelta(days=30)
            active_users = User.objects.filter(
                last_login__gte=thirty_days_ago
            ).count()
            
            # Content metrics
            total_quizzes = Quiz.objects.filter(is_published=True).count()
            total_questions = Question.objects.count()
            total_attempts = UserQuizAttempt.objects.count()
            
            # Popular categories
            popular_categories = []
            category_stats = (
                Quiz.objects
                .filter(is_published=True)
                .values('category__name')
                .annotate(
                    quiz_count=Count('id'),
                    total_attempts=Count('userquizattempt')
                )
                .order_by('-quiz_count')[:10]
            )
            
            for stat in category_stats:
                if stat['category__name']:
                    popular_categories.append({
                        'name': stat['category__name'],
                        'quiz_count': stat['quiz_count'],
                        'attempt_count': stat['total_attempts']
                    })
            
            # User engagement trends
            engagement_trends = self._get_engagement_trends()
            
            result = PlatformAnalytics(
                total_users=total_users,
                active_users_last_30_days=active_users,
                total_quizzes=total_quizzes,
                total_questions=total_questions,
                total_quiz_attempts=total_attempts,
                popular_categories=popular_categories,
                user_engagement_trends=engagement_trends
            )
            
            # Cache result
            cache.set(cache_key, result.__dict__, self.cache_timeout)
            return result
            
        except Exception as e:
            logger.error(f"Failed to get platform analytics: {str(e)}")
            return PlatformAnalytics(0, 0, 0, 0, 0, [], {})
    
    def get_comparative_analytics(self, quiz) -> Dict[str, Any]:
        """Get comparative analytics for a quiz against similar quizzes"""
        try:
            from quizzes.models import Quiz, UserQuizAttempt
            
            # Find similar quizzes (same category and difficulty)
            similar_quizzes = Quiz.objects.filter(
                category=quiz.category,
                difficulty=quiz.difficulty,
                is_published=True
            ).exclude(id=quiz.id)
            
            if not similar_quizzes.exists():
                return {'message': 'No similar quizzes found for comparison'}
            
            # Get metrics for current quiz
            current_metrics = self.get_quiz_analytics(quiz)
            
            # Get aggregated metrics for similar quizzes
            similar_attempts = UserQuizAttempt.objects.filter(
                quiz__in=similar_quizzes,
                is_completed=True
            )
            
            if not similar_attempts.exists():
                return {'message': 'No data available for similar quizzes'}
            
            avg_score_similar = similar_attempts.aggregate(
                avg_score=Avg('percentage')
            )['avg_score'] or 0
            
            avg_time_similar = similar_attempts.exclude(
                time_taken__isnull=True
            ).aggregate(
                avg_time=Avg('time_taken')
            )['avg_time'] or 0
            
            completion_rate_similar = self._calculate_completion_rate_for_quizzes(similar_quizzes)
            
            return {
                'current_quiz': {
                    'average_score': current_metrics.average_score,
                    'average_time': current_metrics.average_time,
                    'completion_rate': current_metrics.completion_rate,
                    'total_attempts': current_metrics.total_attempts
                },
                'similar_quizzes': {
                    'average_score': avg_score_similar,
                    'average_time': int(avg_time_similar),
                    'completion_rate': completion_rate_similar,
                    'total_count': similar_quizzes.count()
                },
                'comparisons': {
                    'score_percentile': self._calculate_percentile(
                        current_metrics.average_score, 
                        avg_score_similar
                    ),
                    'difficulty_relative': self._compare_difficulty(
                        current_metrics.difficulty_rating,
                        similar_quizzes
                    )
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get comparative analytics: {str(e)}")
            return {'error': str(e)}
    
    def generate_insights(self, quiz) -> List[Dict[str, str]]:
        """Generate actionable insights for a quiz"""
        insights = []
        metrics = self.get_quiz_analytics(quiz, detailed=True)
        
        try:
            # Low completion rate insight
            if metrics.completion_rate < 70:
                insights.append({
                    'type': 'warning',
                    'title': 'Low Completion Rate',
                    'message': f'Only {metrics.completion_rate:.1f}% of users complete this quiz. Consider reviewing question difficulty or length.',
                    'action': 'Review quiz structure and difficulty'
                })
            
            # High/Low average score insights
            if metrics.average_score > 90:
                insights.append({
                    'type': 'info',
                    'title': 'High Success Rate',
                    'message': f'Users score {metrics.average_score:.1f}% on average. This quiz might be too easy.',
                    'action': 'Consider increasing difficulty or adding more challenging questions'
                })
            elif metrics.average_score < 50:
                insights.append({
                    'type': 'warning',
                    'title': 'Low Success Rate',
                    'message': f'Average score is only {metrics.average_score:.1f}%. This quiz might be too difficult.',
                    'action': 'Review question difficulty and provide more explanations'
                })
            
            # Time-based insights
            if metrics.average_time > 0:
                expected_time = quiz.time_limit * 60 if quiz.time_limit else len(quiz.questions.all()) * 90
                if metrics.average_time > expected_time * 1.5:
                    insights.append({
                        'type': 'info',
                        'title': 'Longer Than Expected',
                        'message': f'Users take {metrics.average_time//60} minutes on average, longer than expected.',
                        'action': 'Consider simplifying questions or providing clearer instructions'
                    })
            
            # Question-specific insights
            if metrics.question_analytics:
                problematic_questions = [
                    q_id for q_id, data in metrics.question_analytics.items()
                    if data.get('correct_rate', 100) < 30
                ]
                
                if problematic_questions:
                    insights.append({
                        'type': 'warning',
                        'title': 'Difficult Questions Detected',
                        'message': f'{len(problematic_questions)} questions have low success rates.',
                        'action': 'Review and possibly revise these questions'
                    })
            
            # Engagement insights
            if metrics.unique_users > 0 and metrics.total_attempts / metrics.unique_users > 2:
                insights.append({
                    'type': 'success',
                    'title': 'High Re-engagement',
                    'message': 'Users frequently retake this quiz, indicating good engagement.',
                    'action': 'Consider creating similar quizzes or a series'
                })
            
            return insights
            
        except Exception as e:
            logger.error(f"Failed to generate insights: {str(e)}")
            return [{
                'type': 'error',
                'title': 'Analysis Error',
                'message': 'Unable to generate insights at this time.',
                'action': 'Please try again later'
            }]
    
    def _get_question_analytics(self, quiz, attempts) -> Dict[str, Any]:
        """Get detailed analytics for each question in the quiz"""
        question_analytics = {}
        
        try:
            for question in quiz.questions.all():
                # This would require storing individual question responses
                # For now, return placeholder data
                question_analytics[str(question.id)] = {
                    'correct_rate': 75.0,  # Placeholder
                    'average_time': 45,    # Placeholder
                    'skip_rate': 5.0,      # Placeholder
                    'most_common_wrong_answer': 'B'  # Placeholder
                }
            
        except Exception as e:
            logger.error(f"Failed to get question analytics: {str(e)}")
        
        return question_analytics
    
    def _calculate_difficulty_rating(self, average_score: float, completion_rate: float) -> float:
        """Calculate difficulty rating based on score and completion rate"""
        # Difficulty scale: 1 (very easy) to 5 (very hard)
        score_factor = (100 - average_score) / 20  # 0-5 scale
        completion_factor = (100 - completion_rate) / 20  # 0-5 scale
        
        # Weight score more heavily than completion rate
        difficulty = (score_factor * 0.7) + (completion_factor * 0.3)
        
        return min(5.0, max(1.0, difficulty))
    
    def _analyze_learning_progress(self, attempts) -> Dict[str, Any]:
        """Analyze user's learning progress over time"""
        try:
            # Sort attempts by date
            sorted_attempts = attempts.order_by('completed_at')
            
            # Calculate trend in scores
            scores = [attempt.percentage for attempt in sorted_attempts]
            
            if len(scores) < 2:
                return {'trend': 'insufficient_data'}
            
            # Simple linear trend calculation
            x = list(range(len(scores)))
            n = len(scores)
            sum_x = sum(x)
            sum_y = sum(scores)
            sum_xy = sum(x[i] * scores[i] for i in range(n))
            sum_x2 = sum(x[i] ** 2 for i in range(n))
            
            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
            
            trend = 'improving' if slope > 0.5 else 'declining' if slope < -0.5 else 'stable'
            
            return {
                'trend': trend,
                'slope': slope,
                'recent_average': sum(scores[-5:]) / min(5, len(scores)),
                'all_time_average': sum(scores) / len(scores),
                'total_quizzes': len(scores)
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze learning progress: {str(e)}")
            return {'trend': 'error'}
    
    def _get_engagement_trends(self) -> Dict[str, Any]:
        """Get user engagement trends"""
        try:
            from quizzes.models import UserQuizAttempt
            
            # Get daily quiz attempts for the last 30 days
            thirty_days_ago = timezone.now() - timedelta(days=30)
            
            daily_attempts = (
                UserQuizAttempt.objects
                .filter(created_at__gte=thirty_days_ago)
                .extra({'date': 'date(created_at)'})
                .values('date')
                .annotate(count=Count('id'))
                .order_by('date')
            )
            
            # Convert to format suitable for charts
            trends = {
                'daily_attempts': [
                    {'date': item['date'].isoformat(), 'count': item['count']}
                    for item in daily_attempts
                ],
                'peak_day': max(daily_attempts, key=lambda x: x['count']) if daily_attempts else None,
                'average_daily': sum(item['count'] for item in daily_attempts) / len(daily_attempts) if daily_attempts else 0
            }
            
            return trends
            
        except Exception as e:
            logger.error(f"Failed to get engagement trends: {str(e)}")
            return {}
    
    def _calculate_completion_rate_for_quizzes(self, quizzes) -> float:
        """Calculate average completion rate for a set of quizzes"""
        try:
            from quizzes.models import UserQuizAttempt
            
            total_started = UserQuizAttempt.objects.filter(quiz__in=quizzes).count()
            total_completed = UserQuizAttempt.objects.filter(
                quiz__in=quizzes, 
                is_completed=True
            ).count()
            
            if total_started == 0:
                return 0
            
            return (total_completed / total_started) * 100
            
        except Exception as e:
            logger.error(f"Failed to calculate completion rate: {str(e)}")
            return 0
    
    def _calculate_percentile(self, value: float, comparison_value: float) -> int:
        """Calculate percentile ranking"""
        if comparison_value == 0:
            return 50
        
        ratio = value / comparison_value
        
        if ratio >= 1.2:
            return 90
        elif ratio >= 1.1:
            return 75
        elif ratio >= 0.9:
            return 50
        elif ratio >= 0.8:
            return 25
        else:
            return 10
    
    def _compare_difficulty(self, current_difficulty: float, similar_quizzes) -> str:
        """Compare difficulty against similar quizzes"""
        # This would require more complex analysis
        # For now, return a simple comparison
        if current_difficulty > 4:
            return "harder than average"
        elif current_difficulty < 2:
            return "easier than average"
        else:
            return "average difficulty"

# Global instance
analytics_service = AnalyticsService()
