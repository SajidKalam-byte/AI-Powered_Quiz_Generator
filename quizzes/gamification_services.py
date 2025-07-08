from django.db.models import Q, Count, Avg
from django.utils import timezone
from datetime import timedelta
from .gamification_models import (
    Achievement, UserAchievement, UserProgress, Badge, UserBadge,
    Leaderboard, QuizLike, QuizComment
)


class AchievementService:
    """Service class for handling achievement logic"""
    
    @staticmethod
    def get_or_create_user_progress(user):
        """Get or create user progress object"""
        progress, created = UserProgress.objects.get_or_create(
            user=user,
            defaults={
                'total_quizzes_completed': 0,
                'total_quizzes_created': 0,
                'total_attempts': 0,
                'total_points': 0,
                'best_score': 0.0,
                'average_score': 0.0,
                'current_daily_streak': 0,
                'longest_daily_streak': 0,
                'level': 1,
                'experience_points': 0,
            }
        )
        return progress
    
    @classmethod
    def check_achievements(cls, user, trigger_type, **kwargs):
        """Check and award achievements based on user activity"""
        progress = cls.get_or_create_user_progress(user)
        awarded_achievements = []
        
        # Get all active achievements that the user hasn't earned yet
        earned_achievement_ids = UserAchievement.objects.filter(
            user=user
        ).values_list('achievement_id', flat=True)
        
        available_achievements = Achievement.objects.filter(
            is_active=True
        ).exclude(id__in=earned_achievement_ids)
        
        for achievement in available_achievements:
            if cls._check_achievement_criteria(achievement, progress, trigger_type, **kwargs):
                user_achievement = UserAchievement.objects.create(
                    user=user,
                    achievement=achievement,
                    progress_when_earned=getattr(progress, achievement.criteria_type, 0)
                )
                
                # Award points
                progress.add_experience(achievement.points_reward)
                
                awarded_achievements.append(achievement)
        
        return awarded_achievements
    
    @staticmethod
    def _check_achievement_criteria(achievement, progress, trigger_type, **kwargs):
        """Check if achievement criteria is met"""
        criteria_type = achievement.criteria_type
        criteria_value = achievement.criteria_value
        
        # Quiz completion achievements
        if criteria_type == 'quizzes_completed':
            return progress.total_quizzes_completed >= criteria_value
        
        # Quiz creation achievements
        elif criteria_type == 'quizzes_created':
            return progress.total_quizzes_created >= criteria_value
        
        # Perfect score achievements
        elif criteria_type == 'perfect_score':
            return progress.total_perfect_scores >= criteria_value
        
        # High score achievements (90%+)
        elif criteria_type == 'high_scores':
            return progress.total_high_scores >= criteria_value
        
        # Daily streak achievements
        elif criteria_type == 'daily_streak':
            return progress.current_daily_streak >= criteria_value
        
        # Specific trigger-based achievements
        elif criteria_type == 'first_quiz' and trigger_type == 'quiz_completed':
            return progress.total_quizzes_completed == 1
        
        elif criteria_type == 'first_created_quiz' and trigger_type == 'quiz_created':
            return progress.total_quizzes_created == 1
        
        return False
    
    @classmethod
    def update_quiz_completion_stats(cls, user, quiz_attempt):
        """Update user stats when a quiz is completed"""
        progress = cls.get_or_create_user_progress(user)
        
        # Update basic stats
        progress.total_quizzes_completed += 1
        progress.total_attempts += 1
        
        # Update scores
        score = quiz_attempt.score
        if score > progress.best_score:
            progress.best_score = score
        
        # Recalculate average score
        from quizzes.models import UserQuizAttempt
        avg_score = UserQuizAttempt.objects.filter(
            user=user,
            status='COMPLETED'
        ).aggregate(avg_score=Avg('score'))['avg_score'] or 0.0
        progress.average_score = avg_score
        
        # Check for perfect and high scores
        if score == 100.0:
            progress.total_perfect_scores += 1
        elif score >= 90.0:
            progress.total_high_scores += 1
        
        # Update streak
        progress.update_streak()
        
        # Add experience points based on performance
        base_points = 10
        bonus_points = int(score / 10)  # 1 point per 10% score
        if score == 100.0:
            bonus_points += 20  # Perfect score bonus
        
        progress.add_experience(base_points + bonus_points)
        progress.save()
        
        # Check for achievements
        return cls.check_achievements(user, 'quiz_completed', 
                                    score=score, 
                                    quiz_attempt=quiz_attempt)
    
    @classmethod
    def update_quiz_creation_stats(cls, user, quiz):
        """Update user stats when a quiz is created"""
        progress = cls.get_or_create_user_progress(user)
        
        progress.total_quizzes_created += 1
        progress.add_experience(25)  # Base points for creating a quiz
        progress.save()
        
        # Check for achievements
        return cls.check_achievements(user, 'quiz_created', quiz=quiz)
    
    @classmethod
    def check_level_achievements(cls, user, old_level, new_level):
        """Check for level-based achievements"""
        # You can implement level-specific achievements here
        pass
    
    @staticmethod
    def get_user_achievements(user):
        """Get all achievements earned by a user"""
        return UserAchievement.objects.filter(user=user).select_related('achievement').order_by('-earned_at')
    
    @staticmethod
    def get_user_badges(user):
        """Get all badges earned by a user"""
        return UserBadge.objects.filter(user=user).select_related('badge').order_by('-earned_at')
    
    @staticmethod
    def award_badge(user, badge, awarded_by=None, reason=""):
        """Manually award a badge to a user"""
        user_badge, created = UserBadge.objects.get_or_create(
            user=user,
            badge=badge,
            defaults={
                'awarded_by': awarded_by,
                'reason': reason
            }
        )
        
        if created:
            # Award experience points
            progress = AchievementService.get_or_create_user_progress(user)
            progress.add_experience(badge.points_value)
        
        return user_badge, created


class LeaderboardService:
    """Service class for managing leaderboards"""
    
    @staticmethod
    def get_global_leaderboard(leaderboard_type='points', limit=10):
        """Get global leaderboard for specified type"""
        try:
            leaderboard = Leaderboard.objects.get(
                leaderboard_type=leaderboard_type,
                is_active=True
            )
            return leaderboard.get_top_users(limit)
        except Leaderboard.DoesNotExist:
            return UserProgress.objects.none()
    
    @staticmethod
    def get_user_rank(user, leaderboard_type='points'):
        """Get user's rank in a specific leaderboard"""
        try:
            progress = UserProgress.objects.get(user=user)
            
            if leaderboard_type == 'points':
                higher_users = UserProgress.objects.filter(
                    total_points__gt=progress.total_points
                ).count()
            elif leaderboard_type == 'quizzes_completed':
                higher_users = UserProgress.objects.filter(
                    total_quizzes_completed__gt=progress.total_quizzes_completed
                ).count()
            elif leaderboard_type == 'average_score':
                higher_users = UserProgress.objects.filter(
                    average_score__gt=progress.average_score,
                    total_quizzes_completed__gte=5
                ).count()
            else:
                return None
            
            return higher_users + 1
        except UserProgress.DoesNotExist:
            return None
    
    @staticmethod
    def get_weekly_leaderboard(limit=10):
        """Get weekly points leaderboard"""
        week_ago = timezone.now() - timedelta(days=7)
        
        # This would require tracking weekly points separately
        # For now, return regular points leaderboard
        return LeaderboardService.get_global_leaderboard('points', limit)
    
    @staticmethod
    def get_category_leaderboard(category, limit=10):
        """Get leaderboard for a specific category"""
        from django.db.models import Sum, Count
        from quizzes.models import UserQuizAttempt, Quiz
        
        # Get users with highest scores in this category
        category_performers = UserQuizAttempt.objects.filter(
            quiz__category=category,
            status='COMPLETED'
        ).values('user').annotate(
            avg_score=Avg('score'),
            total_attempts=Count('id')
        ).filter(total_attempts__gte=3).order_by('-avg_score')[:limit]
        
        return category_performers


class SocialService:
    """Service class for social features"""
    
    @staticmethod
    def like_quiz(user, quiz):
        """Like a quiz"""
        like, created = QuizLike.objects.get_or_create(
            user=user,
            quiz=quiz
        )
        
        if created:
            # Update quiz creator's social stats
            if quiz.created_by != user:
                progress = AchievementService.get_or_create_user_progress(quiz.created_by)
                progress.total_quiz_likes_received += 1
                progress.save()
        
        return like, created
    
    @staticmethod
    def unlike_quiz(user, quiz):
        """Unlike a quiz"""
        try:
            like = QuizLike.objects.get(user=user, quiz=quiz)
            like.delete()
            
            # Update quiz creator's social stats
            if quiz.created_by != user:
                progress = AchievementService.get_or_create_user_progress(quiz.created_by)
                progress.total_quiz_likes_received = max(0, progress.total_quiz_likes_received - 1)
                progress.save()
            
            return True
        except QuizLike.DoesNotExist:
            return False
    
    @staticmethod
    def comment_on_quiz(user, quiz, text):
        """Add a comment to a quiz"""
        comment = QuizComment.objects.create(
            user=user,
            quiz=quiz,
            text=text
        )
        
        # Update user's social stats
        progress = AchievementService.get_or_create_user_progress(user)
        progress.total_comments_made += 1
        progress.add_experience(5)  # Small XP reward for engagement
        progress.save()
        
        return comment
    
    @staticmethod
    def get_quiz_social_stats(quiz):
        """Get social statistics for a quiz"""
        return {
            'likes_count': quiz.likes.count(),
            'comments_count': quiz.comments.filter(is_approved=True).count(),
        }
    
    @staticmethod
    def get_user_liked_quizzes(user):
        """Get quizzes liked by a user"""
        return QuizLike.objects.filter(user=user).select_related('quiz')


class GamificationDashboard:
    """Service for gamification dashboard data"""
    
    @staticmethod
    def get_user_dashboard_data(user):
        """Get comprehensive gamification data for a user"""
        progress = AchievementService.get_or_create_user_progress(user)
        achievements = AchievementService.get_user_achievements(user)
        badges = AchievementService.get_user_badges(user)
        
        # Get recent achievements (last 30 days)
        recent_achievements = achievements.filter(
            earned_at__gte=timezone.now() - timedelta(days=30)
        )
        
        # Get next achievements to unlock
        earned_achievement_ids = achievements.values_list('achievement_id', flat=True)
        next_achievements = Achievement.objects.filter(
            is_active=True
        ).exclude(id__in=earned_achievement_ids)[:5]
        
        # Calculate progress towards next level
        current_level_xp = (progress.level ** 2) * 100
        next_level_xp = ((progress.level + 1) ** 2) * 100
        level_progress = ((progress.experience_points - current_level_xp) / 
                         (next_level_xp - current_level_xp)) * 100
        
        # Get leaderboard position
        rank = LeaderboardService.get_user_rank(user, 'points')
        
        return {
            'progress': progress,
            'achievements': achievements,
            'badges': badges,
            'recent_achievements': recent_achievements,
            'next_achievements': next_achievements,
            'level_progress': max(0, min(100, level_progress)),
            'current_level_xp': current_level_xp,
            'next_level_xp': next_level_xp,
            'rank': rank,
        }
