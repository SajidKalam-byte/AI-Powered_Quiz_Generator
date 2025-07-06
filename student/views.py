from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from textprocessor.models import UploadedFile
from quizzes.models import Quiz

@login_required
def student_home(request):
    """
    Student-specific home page with personalized content.
    """
    user = request.user
    
    # Get user's uploaded files
    user_files = UploadedFile.objects.filter(user=user)
    recent_files = user_files.order_by('-uploaded_at')[:5]
    
    # Calculate statistics
    uploaded_files_count = user_files.count()
    ai_generated_quizzes = Quiz.objects.filter(created_by=user).count()
    
    context = {
        'recent_files': recent_files,
        'uploaded_files_count': uploaded_files_count,
        'ai_generated_quizzes': ai_generated_quizzes,
        'quizzes_completed': 0,  # TODO: Implement quiz attempts tracking
    }
    
    return render(request, 'student/home.html', context)
