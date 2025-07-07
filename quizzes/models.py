from django.db import models
from django.conf import settings
from django.core.validators import MinLengthValidator, MaxLengthValidator
from django.utils import timezone
from datetime import timedelta
import uuid

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True, validators=[MinLengthValidator(3)])
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, default='bi-book')  # Bootstrap icon class
    color = models.CharField(max_length=20, default='primary')  # Bootstrap color class
    is_active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "categories"
        ordering = ['name']

class Quiz(models.Model):
    DIFFICULTY_CHOICES = [
        ('EASY', 'Easy'),
        ('MEDIUM', 'Medium'),
        ('HARD', 'Hard'),
    ]
    
    QUIZ_TYPE_CHOICES = [
        ('REGULAR', 'Regular Quiz'),
        ('DAILY', 'Daily Challenge'),
        ('FEATURED', 'Featured Quiz'),
        ('AI_GENERATED', 'AI Generated'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200, validators=[MinLengthValidator(5)])
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    description = models.TextField(blank=True, help_text="Brief description of the quiz")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='quizzes')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_quizzes')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_published = models.BooleanField(default=False)
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='MEDIUM')
    quiz_type = models.CharField(max_length=20, choices=QUIZ_TYPE_CHOICES, default='REGULAR')
    time_limit = models.PositiveIntegerField(default=30, help_text="Time limit in minutes")
    max_attempts = models.PositiveIntegerField(default=3, help_text="Maximum attempts per user")
    points_reward = models.PositiveIntegerField(default=100, help_text="Points awarded for completion")
    featured_until = models.DateTimeField(null=True, blank=True)
    tags = models.CharField(max_length=200, blank=True, help_text="Comma-separated tags")
    
    # Statistics
    total_attempts = models.PositiveIntegerField(default=0)
    total_completions = models.PositiveIntegerField(default=0)
    average_score = models.FloatField(default=0.0)

    @property
    def question_count(self):
        return self.questions.count()
    
    @property
    def completion_rate(self):
        if self.total_attempts == 0:
            return 0
        return round((self.total_completions / self.total_attempts) * 100, 1)
    
    @property
    def difficulty_badge_class(self):
        return {
            'EASY': 'success',
            'MEDIUM': 'warning', 
            'HARD': 'danger'
        }.get(self.difficulty, 'secondary')

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            base_slug = slugify(self.title)
            self.slug = base_slug
            counter = 1
            while Quiz.objects.filter(slug=self.slug).exclude(id=self.id).exists():
                self.slug = f"{base_slug}-{counter}"
                counter += 1
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    class Meta:
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['category', 'is_published']),
            models.Index(fields=['quiz_type', 'is_published']),
            models.Index(fields=['featured_until']),
        ]
        ordering = ['-created_at']

class Question(models.Model):
    QUESTION_TYPES = [
        ('MULTIPLE_CHOICE', 'Multiple Choice'),
        ('TRUE_FALSE', 'True/False'),
        ('SHORT_ANSWER', 'Short Answer'),
    ]

    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES, default='MULTIPLE_CHOICE')
    text = models.TextField(validators=[MinLengthValidator(10)])
    option_a = models.CharField(max_length=300, blank=True)
    option_b = models.CharField(max_length=300, blank=True)
    option_c = models.CharField(max_length=300, blank=True)
    option_d = models.CharField(max_length=300, blank=True)
    correct_option = models.CharField(max_length=1, choices=[
        ('A', 'A'),
        ('B', 'B'),
        ('C', 'C'),
        ('D', 'D'),
    ], blank=True)
    correct_answer = models.TextField(blank=True, help_text="For short answer questions")
    explanation = models.TextField(blank=True)
    points = models.PositiveIntegerField(default=10, help_text="Points for correct answer")
    order = models.PositiveIntegerField(default=0)
    difficulty = models.CharField(max_length=20, choices=Quiz.DIFFICULTY_CHOICES, default='MEDIUM')

    def __str__(self):
        return f"Q{self.order}: {self.text[:50]}..."

    class Meta:
        ordering = ['order']
        indexes = [
            models.Index(fields=['quiz', 'order']),
        ]

class UserQuizAttempt(models.Model):
    STATUS_CHOICES = [
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('ABANDONED', 'Abandoned'),
        ('TIME_UP', 'Time Up'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='quiz_attempts')
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='attempts')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='IN_PROGRESS')
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    score = models.PositiveIntegerField(default=0)
    max_possible_score = models.PositiveIntegerField(default=0)
    percentage = models.FloatField(default=0.0)
    time_taken = models.DurationField(null=True, blank=True)  # Time taken to complete
    answers = models.JSONField(default=dict)  # Stores question_id: selected_option
    points_earned = models.PositiveIntegerField(default=0)
    
    @property
    def is_completed(self):
        return self.status == 'COMPLETED'
    
    @property
    def duration_minutes(self):
        if self.time_taken:
            return round(self.time_taken.total_seconds() / 60, 1)
        return 0

    def calculate_score(self):
        """Calculate and update score based on answers"""
        if not self.answers or not self.quiz.questions.exists():
            return
        
        total_points = 0
        earned_points = 0
        correct_answers = 0
        
        for question in self.quiz.questions.all():
            total_points += question.points
            user_answer = self.answers.get(str(question.id))
            
            if user_answer == question.correct_option:
                earned_points += question.points
                correct_answers += 1
        
        self.score = correct_answers
        self.max_possible_score = self.quiz.questions.count()
        self.points_earned = earned_points
        self.percentage = (correct_answers / self.max_possible_score * 100) if self.max_possible_score > 0 else 0
        self.save()

    def __str__(self):
        return f"{self.user.username} - {self.quiz.title} - {self.score}/{self.max_possible_score}"

    class Meta:
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['user', 'quiz']),
            models.Index(fields=['status', 'completed_at']),
        ]

class UserProfile(models.Model):
    """Extended user profile for tracking points and achievements"""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='quiz_profile')
    total_points = models.PositiveIntegerField(default=0)
    total_quizzes_completed = models.PositiveIntegerField(default=0)
    current_streak = models.PositiveIntegerField(default=0)  # Daily quiz streak
    longest_streak = models.PositiveIntegerField(default=0)
    last_quiz_date = models.DateField(null=True, blank=True)
    rank = models.PositiveIntegerField(default=0)
    level = models.PositiveIntegerField(default=1)
    experience_points = models.PositiveIntegerField(default=0)
    
    # Achievement badges
    badges = models.JSONField(default=list, help_text="List of earned badge IDs")
    
    @property
    def next_level_points(self):
        """Points needed for next level"""
        return self.level * 1000  # 1000 points per level
    
    @property
    def progress_to_next_level(self):
        """Progress percentage to next level"""
        points_in_current_level = self.experience_points % 1000
        return (points_in_current_level / 1000) * 100

    def add_points(self, points):
        """Add points and update level"""
        self.total_points += points
        self.experience_points += points
        
        # Check for level up
        new_level = (self.experience_points // 1000) + 1
        if new_level > self.level:
            self.level = new_level
        
        self.save()

    def update_streak(self):
        """Update daily quiz streak"""
        today = timezone.now().date()
        
        if self.last_quiz_date:
            if self.last_quiz_date == today:
                # Already completed today
                return
            elif self.last_quiz_date == today - timedelta(days=1):
                # Consecutive day
                self.current_streak += 1
            else:
                # Streak broken
                self.current_streak = 1
        else:
            # First quiz
            self.current_streak = 1
        
        self.last_quiz_date = today
        if self.current_streak > self.longest_streak:
            self.longest_streak = self.current_streak
        
        self.save()

    def __str__(self):
        return f"{self.user.username} - {self.total_points} points"

    class Meta:
        ordering = ['-total_points']

class DailyChallenge(models.Model):
    """Daily quiz challenges"""
    date = models.DateField(unique=True)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='daily_challenges')
    bonus_points = models.PositiveIntegerField(default=50)
    is_active = models.BooleanField(default=True)
    participants_count = models.PositiveIntegerField(default=0)
    
    @classmethod
    def get_today_challenge(cls):
        """Get or create today's challenge"""
        today = timezone.now().date()
        challenge, created = cls.objects.get_or_create(
            date=today,
            defaults={
                'quiz': cls._get_random_quiz(),
                'bonus_points': 50,
                'is_active': True
            }
        )
        return challenge
    
    @classmethod
    def _get_random_quiz(cls):
        """Get a random published quiz for daily challenge"""
        from django.db.models import Q
        import random
        
        quizzes = Quiz.objects.filter(
            is_published=True,
            quiz_type__in=['REGULAR', 'FEATURED']
        ).exclude(
            quiz_type='DAILY'
        )
        
        if quizzes.exists():
            return random.choice(quizzes)
        return None

    def __str__(self):
        return f"Daily Challenge - {self.date}"

    class Meta:
        ordering = ['-date']

class Leaderboard(models.Model):
    """Leaderboard for different time periods"""
    PERIOD_CHOICES = [
        ('DAILY', 'Daily'),
        ('WEEKLY', 'Weekly'), 
        ('MONTHLY', 'Monthly'),
        ('ALL_TIME', 'All Time'),
    ]
    
    period = models.CharField(max_length=20, choices=PERIOD_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField()
    top_users = models.JSONField(default=list)  # List of user data with rankings
    last_updated = models.DateTimeField(auto_now=True)
    
    @classmethod
    def update_leaderboard(cls, period='DAILY'):
        """Update leaderboard for given period"""
        from django.db.models import Sum, Count
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        today = timezone.now().date()
        
        if period == 'DAILY':
            start_date = today
            end_date = today
        elif period == 'WEEKLY':
            start_date = today - timedelta(days=today.weekday())
            end_date = start_date + timedelta(days=6)
        elif period == 'MONTHLY':
            start_date = today.replace(day=1)
            end_date = (start_date + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        else:  # ALL_TIME
            start_date = timezone.now().date() - timedelta(days=365*10)  # 10 years back
            end_date = today
        
        # Get top users for the period
        users_data = User.objects.filter(
            quiz_attempts__completed_at__date__range=[start_date, end_date],
            quiz_attempts__status='COMPLETED'
        ).annotate(
            period_points=Sum('quiz_attempts__points_earned'),
            period_quizzes=Count('quiz_attempts')
        ).order_by('-period_points')[:50]  # Top 50 users
        
        top_users = []
        for rank, user in enumerate(users_data, 1):
            top_users.append({
                'rank': rank,
                'user_id': user.id,
                'username': user.username,
                'full_name': getattr(user, 'full_name', user.username),
                'points': user.period_points or 0,
                'quizzes_completed': user.period_quizzes or 0,
                'average_score': round((user.period_points or 0) / max(user.period_quizzes or 1, 1), 1)
            })
        
        leaderboard, created = cls.objects.get_or_create(
            period=period,
            start_date=start_date,
            end_date=end_date,
            defaults={'top_users': top_users}
        )
        
        if not created:
            leaderboard.top_users = top_users
            leaderboard.save()
        
        return leaderboard

    def __str__(self):
        return f"{self.period} Leaderboard - {self.start_date} to {self.end_date}"

    class Meta:
        unique_together = ['period', 'start_date', 'end_date']
        ordering = ['-last_updated']