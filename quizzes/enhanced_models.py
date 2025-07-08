"""
Enhanced models for advanced quiz functionality
"""
from django.db import models
from django.conf import settings
from django.core.validators import MinLengthValidator, MaxValueValidator, MinValueValidator
from django.utils import timezone
from django.contrib.postgres.fields import JSONField, ArrayField
from datetime import timedelta
import uuid

class QuizAnalytics(models.Model):
    """Analytics and performance metrics for quizzes"""
    quiz = models.OneToOneField('quizzes.Quiz', on_delete=models.CASCADE, related_name='analytics')
    
    # Performance metrics
    average_score = models.FloatField(default=0.0)
    completion_rate = models.FloatField(default=0.0)
    average_time_taken = models.IntegerField(default=0)  # in seconds
    difficulty_rating = models.FloatField(default=0.0)  # user-rated difficulty 1-5
    
    # Question analytics
    question_stats = models.JSONField(default=dict, blank=True)  # per-question statistics
    
    # Engagement metrics
    total_attempts = models.PositiveIntegerField(default=0)
    unique_users = models.PositiveIntegerField(default=0)
    shares_count = models.PositiveIntegerField(default=0)
    likes_count = models.PositiveIntegerField(default=0)
    
    # AI metrics (if AI-generated)
    ai_quality_score = models.FloatField(null=True, blank=True)
    ai_provider = models.CharField(max_length=50, blank=True)
    generation_metadata = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Quiz analytics"

class QuizTag(models.Model):
    """Tags for better quiz categorization and search"""
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=7, default='#007bff')  # Hex color
    is_featured = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']

class EnhancedQuestion(models.Model):
    """Enhanced question model with additional features"""
    COGNITIVE_LEVELS = [
        ('remember', 'Remember'),
        ('understand', 'Understand'),
        ('apply', 'Apply'),
        ('analyze', 'Analyze'),
        ('evaluate', 'Evaluate'),
        ('create', 'Create'),
    ]
    
    question = models.OneToOneField('quizzes.Question', on_delete=models.CASCADE, related_name='enhanced')
    
    # Enhanced attributes
    cognitive_level = models.CharField(max_length=20, choices=COGNITIVE_LEVELS, default='understand')
    estimated_time = models.PositiveIntegerField(default=90)  # seconds
    topic_tags = ArrayField(models.CharField(max_length=50), default=list, blank=True)
    
    # Analytics
    correct_rate = models.FloatField(default=0.0)  # percentage of correct answers
    average_time_taken = models.FloatField(default=0.0)  # seconds
    skip_rate = models.FloatField(default=0.0)  # percentage of skips
    
    # AI generation metadata
    ai_generated = models.BooleanField(default=False)
    ai_confidence_score = models.FloatField(null=True, blank=True)
    ai_provider = models.CharField(max_length=50, blank=True)
    
    # Question quality metrics
    clarity_score = models.FloatField(null=True, blank=True)
    relevance_score = models.FloatField(null=True, blank=True)
    difficulty_score = models.FloatField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class QuizSession(models.Model):
    """Detailed quiz session tracking"""
    SESSION_STATUS = [
        ('started', 'Started'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('abandoned', 'Abandoned'),
        ('paused', 'Paused'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    quiz = models.ForeignKey('quizzes.Quiz', on_delete=models.CASCADE)
    
    # Session details
    status = models.CharField(max_length=20, choices=SESSION_STATUS, default='started')
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    paused_at = models.DateTimeField(null=True, blank=True)
    total_time_spent = models.PositiveIntegerField(default=0)  # seconds
    
    # Results
    score = models.PositiveIntegerField(default=0)
    total_points = models.PositiveIntegerField(default=0)
    percentage = models.FloatField(default=0.0)
    
    # Detailed tracking
    responses = models.JSONField(default=dict)  # question_id: response_data
    question_times = models.JSONField(default=dict)  # question_id: time_taken
    hints_used = models.JSONField(default=list)  # list of question_ids where hints were used
    
    # Device and context
    user_agent = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    device_type = models.CharField(max_length=20, blank=True)  # mobile, tablet, desktop
    
    class Meta:
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['quiz', 'completed_at']),
        ]

class LearningPath(models.Model):
    """Learning paths for structured quiz progression"""
    name = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey('quizzes.Category', on_delete=models.CASCADE)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    
    # Progression settings
    quizzes = models.ManyToManyField('quizzes.Quiz', through='LearningPathStep')
    min_score_to_advance = models.PositiveIntegerField(default=70)  # percentage
    is_sequential = models.BooleanField(default=True)  # must complete in order
    
    # Metadata
    estimated_duration = models.PositiveIntegerField(help_text="Estimated duration in minutes")
    difficulty_progression = models.CharField(max_length=50, default='progressive')  # progressive, consistent, adaptive
    
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name

class LearningPathStep(models.Model):
    """Individual steps in a learning path"""
    learning_path = models.ForeignKey(LearningPath, on_delete=models.CASCADE)
    quiz = models.ForeignKey('quizzes.Quiz', on_delete=models.CASCADE)
    order = models.PositiveIntegerField()
    
    # Step requirements
    min_score_required = models.PositiveIntegerField(default=70)
    max_attempts = models.PositiveIntegerField(default=3)
    is_optional = models.BooleanField(default=False)
    
    # Unlocking conditions
    prerequisite_steps = models.ManyToManyField('self', blank=True, symmetrical=False)
    
    class Meta:
        ordering = ['learning_path', 'order']
        unique_together = ['learning_path', 'order']

class UserLearningProgress(models.Model):
    """Track user progress through learning paths"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    learning_path = models.ForeignKey(LearningPath, on_delete=models.CASCADE)
    
    # Progress tracking
    current_step = models.ForeignKey(LearningPathStep, on_delete=models.SET_NULL, null=True, blank=True)
    completed_steps = models.ManyToManyField(LearningPathStep, related_name='completed_by')
    
    # Statistics
    started_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    completion_percentage = models.FloatField(default=0.0)
    average_score = models.FloatField(default=0.0)
    total_time_spent = models.PositiveIntegerField(default=0)  # minutes
    
    # Status
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['user', 'learning_path']

class QuizExport(models.Model):
    """Track quiz exports for analytics and caching"""
    EXPORT_FORMATS = [
        ('pdf', 'PDF'),
        ('docx', 'Word Document'),
        ('json', 'JSON'),
        ('csv', 'CSV'),
        ('xlsx', 'Excel'),
    ]
    
    quiz = models.ForeignKey('quizzes.Quiz', on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    
    # Export details
    format = models.CharField(max_length=10, choices=EXPORT_FORMATS)
    include_answers = models.BooleanField(default=True)
    include_explanations = models.BooleanField(default=True)
    include_analytics = models.BooleanField(default=False)
    
    # File details
    file_path = models.FileField(upload_to='exports/', null=True, blank=True)
    file_size = models.PositiveIntegerField(null=True, blank=True)  # bytes
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    downloaded_at = models.DateTimeField(null=True, blank=True)
    download_count = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['-created_at']

class QuizCollaboration(models.Model):
    """Collaborative quiz creation features"""
    PERMISSION_LEVELS = [
        ('view', 'View Only'),
        ('comment', 'Can Comment'),
        ('edit', 'Can Edit'),
        ('admin', 'Administrator'),
    ]
    
    quiz = models.ForeignKey('quizzes.Quiz', on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    permission_level = models.CharField(max_length=20, choices=PERMISSION_LEVELS)
    
    # Invitation details
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='sent_invitations'
    )
    invited_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['quiz', 'user']

class QuizComment(models.Model):
    """Comments and feedback on quizzes"""
    quiz = models.ForeignKey('quizzes.Quiz', on_delete=models.CASCADE, related_name='comments')
    question = models.ForeignKey('quizzes.Question', on_delete=models.CASCADE, null=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    
    # Comment content
    content = models.TextField()
    is_suggestion = models.BooleanField(default=False)  # suggestion for improvement
    is_resolved = models.BooleanField(default=False)
    
    # Thread support
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']

class QuizGameification(models.Model):
    """Gamification elements for quizzes"""
    quiz = models.OneToOneField('quizzes.Quiz', on_delete=models.CASCADE, related_name='gamification')
    
    # Points and rewards
    base_points = models.PositiveIntegerField(default=100)
    bonus_points_speed = models.PositiveIntegerField(default=50)  # for fast completion
    bonus_points_streak = models.PositiveIntegerField(default=25)  # for correct streaks
    
    # Badges
    available_badges = models.JSONField(default=list)  # list of badge configurations
    
    # Leaderboard settings
    enable_leaderboard = models.BooleanField(default=True)
    leaderboard_type = models.CharField(
        max_length=20, 
        choices=[('global', 'Global'), ('friends', 'Friends Only'), ('class', 'Class/Group')],
        default='global'
    )
    
    # Achievements
    enable_achievements = models.BooleanField(default=True)
    achievement_thresholds = models.JSONField(default=dict)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class UserBadge(models.Model):
    """User-earned badges"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    quiz = models.ForeignKey('quizzes.Quiz', on_delete=models.CASCADE)
    
    # Badge details
    badge_type = models.CharField(max_length=50)  # e.g., 'perfect_score', 'speed_demon', 'persistent'
    badge_name = models.CharField(max_length=100)
    badge_description = models.TextField()
    badge_icon = models.CharField(max_length=50)  # icon class or emoji
    
    # Achievement context
    earned_at = models.DateTimeField(auto_now_add=True)
    score_when_earned = models.PositiveIntegerField()
    time_when_earned = models.PositiveIntegerField()  # seconds
    
    class Meta:
        unique_together = ['user', 'quiz', 'badge_type']
        ordering = ['-earned_at']
