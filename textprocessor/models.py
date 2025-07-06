from django.db import models
from django.conf import settings
from django.core.validators import FileExtensionValidator
import os

class UploadedFile(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending Processing'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    FILE_TYPE_CHOICES = [
        ('pdf', 'PDF Document'),
        ('txt', 'Text File'),
        ('docx', 'Word Document'),
        ('pptx', 'PowerPoint'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='uploaded_files')
    file = models.FileField(
        upload_to='uploads/%Y/%m/%d/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'txt', 'docx', 'pptx'])]
    )
    original_filename = models.CharField(max_length=255)
    file_type = models.CharField(max_length=10, choices=FILE_TYPE_CHOICES)
    file_size = models.PositiveIntegerField(help_text="File size in bytes")
    
    # Text processing
    extracted_text = models.TextField(blank=True, null=True)
    processed_topics = models.JSONField(blank=True, null=True, help_text="AI-extracted topics and sections")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Timestamps
    uploaded_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(blank=True, null=True)
    
    # Metadata
    metadata = models.JSONField(blank=True, null=True, help_text="Additional processing metadata")
    error_message = models.TextField(blank=True, null=True)
    
    # Quiz generation tracking
    quizzes_generated = models.IntegerField(default=0)
    
    def __str__(self):
        return f"{self.user.username} - {self.original_filename}"
    
    def save(self, *args, **kwargs):
        if self.file:
            self.original_filename = os.path.basename(self.file.name)
            self.file_size = self.file.size
            # Determine file type from extension
            ext = os.path.splitext(self.file.name)[1].lower()
            type_map = {'.pdf': 'pdf', '.txt': 'txt', '.docx': 'docx', '.pptx': 'pptx'}
            self.file_type = type_map.get(ext, 'txt')
        super().save(*args, **kwargs)
    
    @property
    def file_size_mb(self):
        return round(self.file_size / (1024 * 1024), 2)
    
    @property
    def has_extracted_text(self):
        return bool(self.extracted_text and self.extracted_text.strip())
    
    @property
    def topic_count(self):
        if self.processed_topics:
            return len(self.processed_topics.get('topics', []))
        return 0

    class Meta:
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['uploaded_at']),
        ]


class GeneratedQuiz(models.Model):
    """Track quizzes generated from uploaded files"""
    uploaded_file = models.ForeignKey(UploadedFile, on_delete=models.CASCADE, related_name='generated_quizzes')
    quiz = models.ForeignKey('quizzes.Quiz', on_delete=models.CASCADE)
    topic_used = models.CharField(max_length=200, help_text="Topic from file used to generate quiz")
    generation_method = models.CharField(max_length=50, choices=[
        ('full_text', 'Full Document'),
        ('topic_section', 'Specific Topic Section'),
        ('summary', 'Document Summary'),
    ])
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
