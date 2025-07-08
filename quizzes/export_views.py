"""
Enhanced views for quiz export functionality
"""
import logging
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse, Http404
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.utils import timezone

from quizzes.models import Quiz
from .export_service import quiz_export_service

logger = logging.getLogger(__name__)

@login_required
def export_quiz_form(request, quiz_id):
    """Display export options form"""
    quiz = get_object_or_404(Quiz, id=quiz_id)
    
    # Check permissions
    if not (quiz.created_by == request.user or 
           request.user.is_staff or 
           quiz.is_published):
        raise PermissionDenied("You don't have permission to export this quiz")
    
    context = {
        'quiz': quiz,
        'supported_formats': quiz_export_service.supported_formats,
        'dashboard_template': 'base/dashboard_base.html'  # Adjust based on user type
    }
    
    return render(request, 'quizzes/export_form.html', context)

@login_required
@require_http_methods(["POST"])
def export_quiz(request, quiz_id):
    """Export quiz in specified format"""
    quiz = get_object_or_404(Quiz, id=quiz_id)
    
    # Check permissions
    if not (quiz.created_by == request.user or 
           request.user.is_staff or 
           quiz.is_published):
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    try:
        # Get export options
        format_type = request.POST.get('format', 'pdf').lower()
        include_answers = request.POST.get('include_answers') == 'on'
        include_explanations = request.POST.get('include_explanations') == 'on'
        include_analytics = request.POST.get('include_analytics') == 'on'
        include_metadata = request.POST.get('include_metadata', 'on') == 'on'
        
        # Validate format
        if format_type not in quiz_export_service.supported_formats:
            return JsonResponse({'error': f'Unsupported format: {format_type}'}, status=400)
        
        # Generate export
        export_result = quiz_export_service.export_quiz(
            quiz=quiz,
            format_type=format_type,
            user=request.user,
            include_answers=include_answers,
            include_explanations=include_explanations,
            include_analytics=include_analytics,
            include_metadata=include_metadata
        )
        
        # Return file response
        response = HttpResponse(
            export_result['content'],
            content_type=export_result['content_type']
        )
        response['Content-Disposition'] = f'attachment; filename="{export_result["filename"]}"'
        
        # Add success message for next request
        messages.success(request, f'Quiz exported successfully as {format_type.upper()}')
        
        return response
        
    except ValueError as e:
        logger.error(f"Export validation error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=400)
    except Exception as e:
        logger.error(f"Export failed: {str(e)}")
        return JsonResponse({'error': 'Export failed. Please try again.'}, status=500)

@login_required
def preview_quiz_export(request, quiz_id, format):
    """Preview quiz export in specified format"""
    quiz = get_object_or_404(Quiz, id=quiz_id)
    
    # Check permissions
    if not (quiz.created_by == request.user or 
           request.user.is_staff or 
           quiz.is_published):
        raise PermissionDenied("You don't have permission to preview this quiz")
    
    try:
        # Get preview options
        include_answers = request.GET.get('answers', 'true').lower() == 'true'
        include_explanations = request.GET.get('explanations', 'true').lower() == 'true'
        include_analytics = request.GET.get('analytics', 'false').lower() == 'true'
        
        # Generate preview
        if format.lower() == 'html':
            export_result = quiz_export_service.export_quiz(
                quiz=quiz,
                format_type='html',
                user=request.user,
                include_answers=include_answers,
                include_explanations=include_explanations,
                include_analytics=include_analytics
            )
            return HttpResponse(export_result['content'], content_type='text/html')
        else:
            return JsonResponse({'error': 'Preview only available for HTML format'}, status=400)
        
    except Exception as e:
        logger.error(f"Preview failed: {str(e)}")
        return HttpResponse(f"Preview failed: {str(e)}", status=500)

@login_required
def export_preview(request, quiz_id):
    """Preview quiz export in HTML format"""
    quiz = get_object_or_404(Quiz, id=quiz_id)
    
    # Check permissions
    if not (quiz.created_by == request.user or 
           request.user.is_staff or 
           quiz.is_published):
        raise PermissionDenied("You don't have permission to preview this quiz")
    
    try:
        # Get preview options
        include_answers = request.GET.get('answers', 'true').lower() == 'true'
        include_explanations = request.GET.get('explanations', 'true').lower() == 'true'
        include_analytics = request.GET.get('analytics', 'false').lower() == 'true'
        
        # Generate HTML preview
        export_result = quiz_export_service.export_quiz(
            quiz=quiz,
            format_type='html',
            user=request.user,
            include_answers=include_answers,
            include_explanations=include_explanations,
            include_analytics=include_analytics
        )
        
        return HttpResponse(export_result['content'], content_type='text/html')
        
    except Exception as e:
        logger.error(f"Preview failed: {str(e)}")
        return HttpResponse(f"Preview failed: {str(e)}", status=500)

@login_required
def export_history(request):
    """View export history for user"""
    try:
        from .enhanced_models import QuizExport
        
        exports = QuizExport.objects.filter(user=request.user).order_by('-created_at')[:50]
        
        context = {
            'exports': exports,
            'dashboard_template': 'base/dashboard_base.html'
        }
        
        return render(request, 'quizzes/export_history.html', context)
        
    except ImportError:
        # Enhanced models not available
        return HttpResponse("Export history not available", status=404)

@login_required
def download_export(request, export_id):
    """Re-download a previous export"""
    try:
        from .enhanced_models import QuizExport
        
        export = get_object_or_404(QuizExport, id=export_id, user=request.user)
        
        if not export.file_path:
            return HttpResponse("Export file not found", status=404)
        
        # Update download stats
        export.download_count += 1
        export.downloaded_at = timezone.now()
        export.save()
        
        # Serve file
        with open(export.file_path.path, 'rb') as f:
            response = HttpResponse(
                f.read(),
                content_type='application/octet-stream'
            )
            response['Content-Disposition'] = f'attachment; filename="{export.file_path.name}"'
            return response
            
    except ImportError:
        return HttpResponse("Export download not available", status=404)
    except Exception as e:
        logger.error(f"Download failed: {str(e)}")
        return HttpResponse("Download failed", status=500)
