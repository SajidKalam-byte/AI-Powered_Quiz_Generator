from django.db import models
from django.conf import settings  # Correct import for AUTH_USER_MODEL

class UploadedFile(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='uploaded_files')
    file = models.FileField(upload_to='uploads/%Y/%m/%d/')
    file_type = models.CharField(max_length=10, choices=[('pdf', 'PDF'), ('txt', 'Text')])
    extracted_text = models.TextField(blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(blank=True, null=True)  # For future AI-related metadata

    def __str__(self):
        return f"{self.user.username} - {self.file.name} ({self.uploaded_at})"

    class Meta:
        ordering = ['-uploaded_at']
