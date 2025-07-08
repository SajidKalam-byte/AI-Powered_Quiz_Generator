from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


class Achievement(models.Model):
    """Define various achievements users can earn"""
    ACHIEVEMENT_TYPES = [
        ('quiz_creator', 'Quiz Creator'),
        ('quiz_taker', 'Quiz Taker'),
        ('performance', 'Performance'),
        ('streak', 'Streak'),
        ('social', 'Social'),
        ('special', 'Special'),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    icon = models.CharField(max_length=50, default='bi-award')  # Bootstrap icon class
    achievement_type = models.CharField(max_length=20, choices=ACHIEVEMENT_TYPES)
    points_reward = models.IntegerField(default=0)
    
    # Criteria for earning the achievement
    criteria_type = models.CharField(max_length=50)  # e.g., 'quiz_completed', 'score_achieved'
    criteria_value = models.IntegerField(default=1)  # e.g., number of quizzes, minimum score
    
    # Badge styling
    badge_color = models.CharField(max_length=20, default='primary')
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['achievement_type', 'name']
    
    def __str__(self):
        return self.name
    
    @classmethod
    def create_default_achievements(cls):
        """Create default achievements"""
        default_achievements = [
            # Quiz Creator Achievements
            {
                'name': 'First Quiz Creator',
                'description': 'Created your first quiz',
                'achievement_type': 'quiz_creator',
                'criteria_type': 'quizzes_created',
                'criteria_value': 1,
                'points_reward': 50,
                'icon': 'bi-plus-circle',
                'badge_color': 'success'
            },
            {
                'name': 'Prolific Creator',
                'description': 'Created 10 quizzes',
                'achievement_type': 'quiz_creator',
                'criteria_type': 'quizzes_created',
                'criteria_value': 10,
                'points_reward': 200,
                'icon': 'bi-collection',
                'badge_color': 'info'
            },
            {
                'name': 'Quiz Master',
                'description': 'Created 50 quizzes',
                'achievement_type': 'quiz_creator',
                'criteria_type': 'quizzes_created',
                'criteria_value': 50,
                'points_reward': 1000,
                'icon': 'bi-crown',
                'badge_color': 'warning'
            },
            
            # Quiz Taker Achievements
            {
                'name': 'First Steps',
                'description': 'Completed your first quiz',
                'achievement_type': 'quiz_taker',
                'criteria_type': 'quizzes_completed',
                'criteria_value': 1,
                'points_reward': 25,
                'icon': 'bi-check-circle',
                'badge_color': 'primary'
            },
            {
                'name': 'Quiz Explorer',
                'description': 'Completed 25 quizzes',
                'achievement_type': 'quiz_taker',
                'criteria_type': 'quizzes_completed',
                'criteria_value': 25,
                'points_reward': 150,
                'icon': 'bi-compass',
                'badge_color': 'secondary'
            },
            {
                'name': 'Quiz Addict',
                'description': 'Completed 100 quizzes',
                'achievement_type': 'quiz_taker',
                'criteria_type': 'quizzes_completed',
                'criteria_value': 100,
                'points_reward': 500,
                'icon': 'bi-lightning',
                'badge_color': 'danger'
            },
            
            # Performance Achievements
            {
                'name': 'Perfect Score',
                'description': 'Achieved 100% on a quiz',
                'achievement_type': 'performance',
                'criteria_type': 'perfect_score',
                'criteria_value': 1,
                'points_reward': 100,
                'icon': 'bi-star-fill',
                'badge_color': 'warning'
            },
            {
                'name': 'High Achiever',
                'description': 'Achieved 90%+ on 10 quizzes',
                'achievement_type': 'performance',
                'criteria_type': 'high_scores',
                'criteria_value': 10,
                'points_reward': 300,
                'icon': 'bi-trophy',
                'badge_color': 'success'
            },
            
            # Streak Achievements
            {
                'name': 'On Fire',
                'description': 'Completed quizzes on 7 consecutive days',
                'achievement_type': 'streak',
                'criteria_type': 'daily_streak',
                'criteria_value': 7,
                'points_reward': 200,
                'icon': 'bi-fire',
                'badge_color': 'danger'
            },
            {
                'name': 'Unstoppable',
                'description': 'Completed quizzes on 30 consecutive days',
                'achievement_type': 'streak',
                'criteria_type': 'daily_streak',
                'criteria_value': 30,
                'points_reward': 1000,
                'icon': 'bi-rocket',
                'badge_color': 'warning'
            },
        ]
        
        for achievement_data in default_achievements:
            cls.objects.get_or_create(
                name=achievement_data['name'],
                defaults=achievement_data
            )


class UserAchievement(models.Model):
    """Track achievements earned by users"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='achievements')
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE)
    earned_at = models.DateTimeField(auto_now_add=True)
    
    # Additional context
    progress_when_earned = models.IntegerField(default=0)  # Progress value when earned
    notes = models.TextField(blank=True)
    
    class Meta:
        unique_together = ['user', 'achievement']
        ordering = ['-earned_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.achievement.name}"


class UserProgress(models.Model):
    """Track user progress towards achievements and overall stats"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='progress')
    
    # Quiz statistics
    total_quizzes_completed = models.IntegerField(default=0)
    total_quizzes_created = models.IntegerField(default=0)
    total_attempts = models.IntegerField(default=0)
    total_points = models.IntegerField(default=0)
    
    # Performance metrics
    best_score = models.FloatField(default=0.0)
    average_score = models.FloatField(default=0.0)
    total_perfect_scores = models.IntegerField(default=0)
    total_high_scores = models.IntegerField(default=0)  # 90%+ scores
    
    # Streak tracking
    current_daily_streak = models.IntegerField(default=0)
    longest_daily_streak = models.IntegerField(default=0)
    last_activity_date = models.DateField(null=True, blank=True)
    
    # Level system
    level = models.IntegerField(default=1)
    experience_points = models.IntegerField(default=0)
    
    # Social metrics
    total_quiz_likes_received = models.IntegerField(default=0)
    total_comments_made = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} Progress"
    
    def update_streak(self):
        """Update daily streak based on recent activity"""
        today = timezone.now().date()
        
        if self.last_activity_date:
            if self.last_activity_date == today:
                # Already updated today
                return
            elif self.last_activity_date == today - timedelta(days=1):
                # Consecutive day
                self.current_daily_streak += 1
            else:
                # Streak broken
                self.current_daily_streak = 1
        else:
            # First activity
            self.current_daily_streak = 1
        
        # Update longest streak
        if self.current_daily_streak > self.longest_daily_streak:
            self.longest_daily_streak = self.current_daily_streak
        
        self.last_activity_date = today
        self.save()
    
    def calculate_level(self):
        """Calculate user level based on experience points"""
        # Simple leveling system: level = sqrt(xp / 100)
        import math
        new_level = max(1, int(math.sqrt(self.experience_points / 100)))
        
        if new_level != self.level:
            old_level = self.level
            self.level = new_level
            self.save()
            
            # Trigger level up achievement check
            from .services import AchievementService
            AchievementService.check_level_achievements(self.user, old_level, new_level)
    
    def add_experience(self, points):
        """Add experience points and update level"""
        self.experience_points += points
        self.total_points += points
        self.calculate_level()
        self.save()


class Badge(models.Model):
    """Special badges that can be awarded to users"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    icon = models.CharField(max_length=50, default='bi-patch-check')
    badge_type = models.CharField(max_length=50, default='special')
    
    # Visual styling
    background_color = models.CharField(max_length=20, default='primary')
    text_color = models.CharField(max_length=20, default='white')
    border_color = models.CharField(max_length=20, default='primary')
    
    # Criteria (optional - some badges may be manually awarded)
    is_auto_awarded = models.BooleanField(default=False)
    criteria_description = models.TextField(blank=True)
    
    # Rarity and value
    rarity = models.CharField(max_length=20, choices=[
        ('common', 'Common'),
        ('uncommon', 'Uncommon'),
        ('rare', 'Rare'),
        ('epic', 'Epic'),
        ('legendary', 'Legendary'),
    ], default='common')
    
    points_value = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['rarity', 'name']
    
    def __str__(self):
        return self.name


class UserBadge(models.Model):
    """Track badges earned by users"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='badges')
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE)
    earned_at = models.DateTimeField(auto_now_add=True)
    awarded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='badges_awarded')
    
    # Context
    reason = models.TextField(blank=True)
    
    class Meta:
        unique_together = ['user', 'badge']
        ordering = ['-earned_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.badge.name}"


class Leaderboard(models.Model):
    """Different types of leaderboards"""
    LEADERBOARD_TYPES = [
        ('points', 'Total Points'),
        ('quizzes_completed', 'Quizzes Completed'),
        ('quizzes_created', 'Quizzes Created'),
        ('average_score', 'Average Score'),
        ('perfect_scores', 'Perfect Scores'),
        ('streak', 'Current Streak'),
        ('weekly_points', 'Weekly Points'),
        ('monthly_points', 'Monthly Points'),
    ]
    
    name = models.CharField(max_length=100)
    leaderboard_type = models.CharField(max_length=30, choices=LEADERBOARD_TYPES, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    # Display settings
    max_entries = models.IntegerField(default=100)
    refresh_interval = models.IntegerField(default=60)  # minutes
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    def get_top_users(self, limit=10):
        """Get top users for this leaderboard type"""
        from django.db.models import Q, F
        
        if self.leaderboard_type == 'points':
            return UserProgress.objects.select_related('user').order_by('-total_points')[:limit]
        elif self.leaderboard_type == 'quizzes_completed':
            return UserProgress.objects.select_related('user').order_by('-total_quizzes_completed')[:limit]
        elif self.leaderboard_type == 'quizzes_created':
            return UserProgress.objects.select_related('user').order_by('-total_quizzes_created')[:limit]
        elif self.leaderboard_type == 'average_score':
            return UserProgress.objects.select_related('user').filter(
                total_quizzes_completed__gte=5
            ).order_by('-average_score')[:limit]
        elif self.leaderboard_type == 'perfect_scores':
            return UserProgress.objects.select_related('user').order_by('-total_perfect_scores')[:limit]
        elif self.leaderboard_type == 'streak':
            return UserProgress.objects.select_related('user').order_by('-current_daily_streak')[:limit]
        else:
            return UserProgress.objects.none()


class QuizLike(models.Model):
    """Track quiz likes for social features"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    quiz = models.ForeignKey('quizzes.Quiz', on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'quiz']
    
    def __str__(self):
        return f"{self.user.username} likes {self.quiz.title}"


class QuizComment(models.Model):
    """Comments on quizzes for social interaction"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    quiz = models.ForeignKey('quizzes.Quiz', on_delete=models.CASCADE, related_name='comments')
    text = models.TextField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Moderation
    is_approved = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Comment by {self.user.username} on {self.quiz.title}"
