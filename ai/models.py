from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class AIPromptTemplate(models.Model):
    """Templates for AI quiz generation prompts"""
    PROMPT_TYPES = [
        ('quiz_generation', 'Quiz Generation'),
        ('question_analysis', 'Question Analysis'),
        ('content_summary', 'Content Summary'),
        ('difficulty_assessment', 'Difficulty Assessment'),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    prompt_type = models.CharField(max_length=50, choices=PROMPT_TYPES)
    template = models.TextField(
        help_text="Use {placeholders} for variable content"
    )
    description = models.TextField(blank=True)
    
    # Configuration
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    
    # Usage tracking
    usage_count = models.IntegerField(default=0)
    
    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['prompt_type', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.get_prompt_type_display()})"
    
    @classmethod
    def get_default_template(cls, prompt_type):
        """Get the default template for a prompt type"""
        try:
            return cls.objects.get(
                prompt_type=prompt_type,
                is_default=True,
                is_active=True
            )
        except cls.DoesNotExist:
            return None
    
    def increment_usage(self):
        """Increment usage counter"""
        self.usage_count += 1
        self.save(update_fields=['usage_count'])


class AIUsageLog(models.Model):
    """Log AI API usage for monitoring and analytics"""
    AI_PROVIDERS = [
        ('gemini', 'Google Gemini'),
        ('openai', 'OpenAI'),
        ('fallback', 'Fallback'),
    ]
    
    REQUEST_TYPES = [
        ('quiz_generation', 'Quiz Generation'),
        ('text_analysis', 'Text Analysis'),
        ('content_summary', 'Content Summary'),
        ('question_validation', 'Question Validation'),
    ]
    
    # Request details
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    provider = models.CharField(max_length=20, choices=AI_PROVIDERS)
    request_type = models.CharField(max_length=30, choices=REQUEST_TYPES)
    prompt_template = models.ForeignKey(
        AIPromptTemplate, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    
    # Input/Output
    input_text_length = models.IntegerField(default=0)
    output_text_length = models.IntegerField(default=0)
    
    # Performance metrics
    response_time_ms = models.IntegerField(default=0)
    tokens_used = models.IntegerField(default=0)
    cost_estimate = models.DecimalField(max_digits=10, decimal_places=6, default=0.0)
    
    # Status
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)
    
    # Metadata
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['provider', 'timestamp']),
            models.Index(fields=['request_type', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.request_type} ({self.provider})"
    
    @classmethod
    def log_usage(cls, user, provider, request_type, **kwargs):
        """Create a usage log entry"""
        return cls.objects.create(
            user=user,
            provider=provider,
            request_type=request_type,
            **kwargs
        )


class AIConfiguration(models.Model):
    """Global AI configuration settings"""
    # API Keys (should be stored in environment variables, this is for backup/override)
    gemini_api_key = models.CharField(max_length=200, blank=True)
    openai_api_key = models.CharField(max_length=200, blank=True)
    
    # Rate limiting
    max_requests_per_user_per_hour = models.IntegerField(default=100)
    max_requests_per_user_per_day = models.IntegerField(default=1000)
    
    # Default settings
    default_temperature = models.FloatField(default=0.7)
    default_max_tokens = models.IntegerField(default=2000)
    
    # Feature flags
    enable_gemini = models.BooleanField(default=True)
    enable_openai = models.BooleanField(default=True)
    enable_fallback = models.BooleanField(default=True)
    
    # Monitoring
    enable_usage_logging = models.BooleanField(default=True)
    enable_cost_tracking = models.BooleanField(default=True)
    
    # Metadata
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        verbose_name = "AI Configuration"
        verbose_name_plural = "AI Configuration"
    
    def save(self, *args, **kwargs):
        # Ensure only one configuration exists
        if not self.pk and AIConfiguration.objects.exists():
            raise ValueError("Only one AI configuration can exist")
        super().save(*args, **kwargs)
    
    @classmethod
    def get_config(cls):
        """Get the AI configuration (create if doesn't exist)"""
        config, created = cls.objects.get_or_create(
            pk=1,
            defaults={
                'max_requests_per_user_per_hour': 100,
                'max_requests_per_user_per_day': 1000,
                'default_temperature': 0.7,
                'default_max_tokens': 2000,
                'enable_gemini': True,
                'enable_openai': True,
                'enable_fallback': True,
                'enable_usage_logging': True,
                'enable_cost_tracking': True,
            }
        )
        return config


class QuizGenerationRequest(models.Model):
    """Track quiz generation requests for analysis"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    # Request details
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    input_content = models.TextField()
    content_type = models.CharField(max_length=50, default='text')  # text, pdf, docx, etc.
    
    # Generation parameters
    num_questions = models.IntegerField(default=10)
    difficulty_level = models.CharField(max_length=20, default='medium')
    question_types = models.JSONField(default=list)  # ['mcq', 'true_false', etc.]
    
    # AI settings used
    ai_provider = models.CharField(max_length=20, default='gemini')
    temperature = models.FloatField(default=0.7)
    max_tokens = models.IntegerField(default=2000)
    
    # Results
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    generated_quiz_id = models.UUIDField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    
    # Performance metrics
    processing_time_seconds = models.FloatField(default=0.0)
    ai_response_time_ms = models.IntegerField(default=0)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Quiz Generation - {self.user.username} ({self.status})"
    
    def mark_completed(self, quiz_id=None):
        """Mark the request as completed"""
        self.status = 'completed'
        self.completed_at = timezone.now()
        if quiz_id:
            self.generated_quiz_id = quiz_id
        self.save()
    
    def mark_failed(self, error_message):
        """Mark the request as failed"""
        self.status = 'failed'
        self.error_message = error_message
        self.completed_at = timezone.now()
        self.save()
