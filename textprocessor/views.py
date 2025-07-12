from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db import transaction
from django.utils import timezone
import os
import logging
import json

from .forms import FileUploadForm, QuizFromFileForm
from .models import UploadedFile, GeneratedQuiz
from .utils import (
    extract_text_from_file, 
    extract_topics_with_ai, 
    validate_extracted_text,
    get_text_chunk_for_quiz
)
from ai.utils import ai_service
from quizzes.models import Quiz, Question, Category
from quizzes.views import get_dashboard_template
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

@login_required
def upload_file(request):
    """Enhanced file upload with better processing"""
    dashboard_template = get_dashboard_template(request.user)
    
    if request.method == 'POST':
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            # Create file instance
            instance = form.save(commit=False)
            instance.user = request.user
            instance.status = 'processing'
            instance.save()
            
            # Process file asynchronously (in real app, use Celery)
            try:
                process_uploaded_file(instance)
                messages.success(request, f'File "{instance.original_filename}" uploaded and processed successfully!')
                return redirect('textprocessor:file_detail', file_id=instance.id)
            except Exception as e:
                instance.status = 'failed'
                instance.error_message = str(e)
                instance.save()
                messages.error(request, f'Error processing file: {str(e)}')
    else:
        form = FileUploadForm()
    
    # Get recent uploads
    recent_files = UploadedFile.objects.filter(user=request.user)[:5]
    
    return render(request, 'textprocessor/upload.html', {
        'form': form,
        'recent_files': recent_files,
        'dashboard_template': dashboard_template
    })

def process_uploaded_file(instance):
    """Process uploaded file - extract text and topics"""
    file_path = instance.file.path
    
    # Extract text
    extracted_text, success = extract_text_from_file(file_path, instance.file_type)
    
    if not success:
        raise Exception(f"Failed to extract text: {extracted_text}")
    
    # Validate extracted text
    validation = validate_extracted_text(extracted_text)
    if not validation['valid']:
        raise Exception(f"Text validation failed: {validation['reason']}")
    
    # Save extracted text
    instance.extracted_text = extracted_text
    instance.status = 'completed'
    instance.processed_at = timezone.now()
    
    # Extract topics using AI
    try:
        topics_data = extract_topics_with_ai(extracted_text)
        instance.processed_topics = topics_data
        
        # Update metadata
        instance.metadata = {
            'validation': validation,
            'processing_method': 'ai_enhanced',
            'topics_extracted': len(topics_data.get('topics', [])),
            'has_structure': bool(topics_data.get('structure', {}).get('chapters'))
        }
    except Exception as e:
        logger.warning(f"AI topic extraction failed for file {instance.id}: {str(e)}")
        instance.metadata = {
            'validation': validation,
            'processing_method': 'basic',
            'ai_extraction_error': str(e)
        }
    
    instance.save()

@login_required
@login_required
def file_list(request):
    """List all uploaded files for the user"""
    dashboard_template = get_dashboard_template(request.user)
    
    files = UploadedFile.objects.filter(user=request.user).order_by('-uploaded_at')
    
    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        files = files.filter(original_filename__icontains=search_query)
    
    # Filter by status if provided
    status_filter = request.GET.get('status')
    if status_filter:
        files = files.filter(status=status_filter)
    
    # Pagination
    paginator = Paginator(files, 12)  # Show 12 files per page for grid layout
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Calculate statistics
    total_files = UploadedFile.objects.filter(user=request.user).count()
    completed_files = UploadedFile.objects.filter(user=request.user, status='completed').count()
    processing_files = UploadedFile.objects.filter(user=request.user, status='processing').count()
    
    # Calculate total topics
    total_topics = 0
    for file in UploadedFile.objects.filter(user=request.user, status='completed'):
        if file.processed_topics and file.processed_topics.get('topics'):
            total_topics += len(file.processed_topics['topics'])
    
    return render(request, 'textprocessor/file_list.html', {
        'files': page_obj,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'total_files': total_files,
        'completed_files': completed_files,
        'processing_files': processing_files,
        'total_topics': total_topics,
        'search_query': search_query,
        'status_filter': status_filter,
        'dashboard_template': dashboard_template
    })

@login_required
def file_detail(request, file_id):
    """Detailed view of uploaded file"""
    file_obj = get_object_or_404(UploadedFile, id=file_id, user=request.user)
    dashboard_template = get_dashboard_template(request.user)
    
    # Get generated quizzes from this file
    generated_quizzes = GeneratedQuiz.objects.filter(uploaded_file=file_obj)
    
    return render(request, 'textprocessor/file_detail.html', {
        'file': file_obj,
        'generated_quizzes': generated_quizzes,
        'dashboard_template': dashboard_template
    })

@login_required
def generate_quiz_from_file(request):
    """Generate quiz from uploaded file"""
    dashboard_template = get_dashboard_template(request.user)
    
    # Pre-select file if provided in URL or POST data
    selected_file_id = request.GET.get('file') or request.POST.get('uploaded_file')
    selected_file = None
    if selected_file_id:
        try:
            selected_file = UploadedFile.objects.get(
                id=selected_file_id, 
                user=request.user, 
                status='completed'
            )
        except UploadedFile.DoesNotExist:
            messages.error(request, 'Selected file not found or not processed.')
    
    if request.method == 'POST':
        form = QuizFromFileForm(user=request.user, data=request.POST)
        if form.is_valid():
            try:
                quiz = create_quiz_from_file_data(request.user, form.cleaned_data)
                messages.success(request, f'Quiz "{quiz.title}" generated successfully!')
                return redirect('quizzes:quiz_detail', quiz_id=quiz.id)
            except Exception as e:
                logger.error(f"Quiz generation failed: {str(e)}")
                messages.error(request, f'Failed to generate quiz: {str(e)}')
    else:
        # Pre-populate form with selected file
        initial_data = {}
        if selected_file:
            initial_data['uploaded_file'] = selected_file.id
        form = QuizFromFileForm(user=request.user, initial=initial_data)
    
    return render(request, 'textprocessor/generate_quiz.html', {
        'form': form,
        'selected_file': selected_file,
        'dashboard_template': dashboard_template
    })

def create_quiz_from_file_data(user, form_data):
    """Create quiz from file data"""
    uploaded_file = form_data['uploaded_file']
    topic_selection = form_data['topic_selection']
    specific_topic = form_data.get('specific_topic', '')
    num_questions = form_data['num_questions']
    difficulty = form_data['difficulty']
    category = form_data.get('category')
    
    # Get text chunk for quiz generation
    text_chunk = get_text_chunk_for_quiz(
        uploaded_file.extracted_text,
        specific_topic,
        topic_selection
    )
    
    if not text_chunk or len(text_chunk) < 100:
        raise Exception("Insufficient text content for quiz generation")
    
    # Determine topic and category
    if topic_selection == 'specific_topic' and specific_topic:
        quiz_topic = specific_topic
    else:
        # Use first topic from processed topics or filename
        if uploaded_file.processed_topics and uploaded_file.processed_topics.get('topics'):
            quiz_topic = uploaded_file.processed_topics['topics'][0]
        else:
            quiz_topic = os.path.splitext(uploaded_file.original_filename)[0]
    
    if not category and uploaded_file.processed_topics:
        # Try to auto-detect category
        suggested_categories = uploaded_file.processed_topics.get('suggested_categories', [])
        if suggested_categories:
            try:
                category = Category.objects.filter(name__icontains=suggested_categories[0]).first()
            except:
                pass
    
    # Generate quiz using AI
    quiz_data = generate_quiz_with_ai(text_chunk, quiz_topic, num_questions, difficulty, category)
    
    # Create quiz in database
    with transaction.atomic():
        quiz = Quiz.objects.create(
            title=quiz_data.get('title', f"Quiz: {quiz_topic}"),
            category=category,
            created_by=user,
            difficulty=difficulty,
            is_published=True
        )
        
        # Create questions
        for idx, q_data in enumerate(quiz_data['questions'], start=1):
            Question.objects.create(
                quiz=quiz,
                text=q_data['text'],
                option_a=q_data['options']['A'],
                option_b=q_data['options']['B'],
                option_c=q_data['options']['C'],
                option_d=q_data['options']['D'],
                correct_option=q_data['correct_option'],
                explanation=q_data.get('explanation', ''),
                order=idx
            )
        
        # Track generation
        GeneratedQuiz.objects.create(
            uploaded_file=uploaded_file,
            quiz=quiz,
            topic_used=quiz_topic,
            generation_method=topic_selection
        )
        
        # Update file stats
        uploaded_file.quizzes_generated += 1
        uploaded_file.save()
    
    return quiz

def generate_quiz_with_ai(text_content, topic, num_questions, difficulty, category=None):
    """Generate quiz using enhanced AI service"""
    try:
        category_name = category.name if category else "General Knowledge"
        
        # Use the enhanced AI service
        quiz_data = ai_service.generate_quiz_questions(
            topic=topic,
            content=text_content,
            num_questions=num_questions,
            difficulty=difficulty,
            question_types=['MULTIPLE_CHOICE'],
            category=category_name
        )
        
        if not quiz_data or 'questions' not in quiz_data:
            raise Exception("AI service returned invalid quiz data")
        
        # Convert to expected format for database storage
        formatted_quiz = {
            'title': quiz_data.get('title', f"Quiz: {topic}"),
            'description': quiz_data.get('description', f"AI-generated quiz on {topic}"),
            'questions': []
        }
        
        for q in quiz_data['questions']:
            if q.get('type') == 'MULTIPLE_CHOICE':
                formatted_question = {
                    'text': q['text'],
                    'options': q['options'],
                    'correct_option': q['correct_option'],
                    'explanation': q.get('explanation', ''),
                    'difficulty': q.get('difficulty', difficulty),
                    'points': q.get('points', 10)
                }
                formatted_quiz['questions'].append(formatted_question)
        
        return formatted_quiz
        
    except Exception as e:
        logger.error(f"Enhanced AI quiz generation failed: {str(e)}")
        # Fallback to original method
        return generate_quiz_with_ai_fallback(text_content, topic, num_questions, difficulty, category)

def generate_quiz_with_ai_fallback(text_content, topic, num_questions, difficulty, category=None):
    """Fallback AI quiz generation method"""
    category_name = category.name if category else "General Knowledge"
    
    prompt = f"""
    Based on the following educational content, generate a quiz with exactly {num_questions} multiple-choice questions about {topic} in the {category_name} category at {difficulty} difficulty level.

    Content:
    {text_content}

    Requirements:
    - All questions MUST be based on the provided content
    - Each question must mention {topic} or related concepts from the content
    - Difficulty level: {difficulty}
    - Category: {category_name}
    - Questions should test understanding of the material
    - Provide clear explanations for correct answers

    Return ONLY valid JSON in this format:
    {{
        "title": "Quiz title based on {topic} and {category_name}",
        "questions": [
            {{
                "text": "Question text based on the content",
                "options": {{"A": "Option A", "B": "Option B", "C": "Option C", "D": "Option D"}},
                "correct_option": "A",
                "explanation": "Explanation based on the content"
            }}
        ]
    }}
    """
    
    try:
        response = requests.post(
            "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent",
            headers={
                'Content-Type': 'application/json',
                'X-goog-api-key': getattr(settings, 'GEMINI_API_KEY', '')
            },
            json={
                "contents": [{"parts": [{"text": prompt}]}]
            },
            timeout=30
        )
        
        if response.status_code == 200:
            raw_text = (
                response.json()
                .get('candidates', [{}])[0]
                .get('content', {})
                .get('parts', [{}])[0]
                .get('text', '')
            )
            
            # Extract JSON from response
            import re
            json_match = re.search(r'(?:```json\s*)?(\{[\s\S]*?\})(?:\s*```)?', raw_text, re.DOTALL)
            if json_match:
                quiz_data = json.loads(json_match.group(1))
                
                # Validate quiz data
                if validate_quiz_data(quiz_data, num_questions):
                    return quiz_data
        
        raise Exception("AI generation failed or returned invalid data")
        
    except Exception as e:
        logger.error(f"AI quiz generation failed: {str(e)}")
        # Return fallback quiz
        return generate_fallback_quiz_from_content(text_content, topic, num_questions, category_name)

def validate_quiz_data(quiz_data, expected_questions):
    """Validate AI-generated quiz data"""
    if not isinstance(quiz_data, dict):
        return False
    
    if 'questions' not in quiz_data:
        return False
    
    questions = quiz_data['questions']
    if not isinstance(questions, list) or len(questions) != expected_questions:
        return False
    
    for q in questions:
        if not all(key in q for key in ['text', 'options', 'correct_option']):
            return False
        
        if not isinstance(q['options'], dict) or set(q['options'].keys()) != {'A', 'B', 'C', 'D'}:
            return False
        
        if q['correct_option'] not in ['A', 'B', 'C', 'D']:
            return False
    
    return True

def generate_fallback_quiz_from_content(text_content, topic, num_questions, category_name):
    """Generate a basic fallback quiz when AI fails"""
    # This is a simple fallback - in production, you'd want a more sophisticated approach
    words = text_content.split()
    
    questions = []
    for i in range(min(num_questions, 5)):  # Limit fallback questions
        question_text = f"Based on the content about {topic}, which of the following is most relevant?"
        
        # Simple options generation (this is very basic)
        options = {
            'A': f"Concept related to {topic}",
            'B': f"Another aspect of {topic}",
            'C': f"Different approach to {topic}",
            'D': f"Alternative view on {topic}"
        }
        
        questions.append({
            'text': question_text,
            'options': options,
            'correct_option': 'A',
            'explanation': f"This answer relates to the main concepts discussed in the {topic} content."
        })
    
    return {
        'title': f"Basic Quiz: {topic}",
        'questions': questions
    }

@login_required
@require_http_methods(["DELETE"])
def delete_file(request, file_id):
    """Delete uploaded file"""
    file_obj = get_object_or_404(UploadedFile, id=file_id, user=request.user)
    
    try:
        # Delete physical file
        if file_obj.file and os.path.exists(file_obj.file.path):
            os.remove(file_obj.file.path)
        
        # Delete database record
        file_obj.delete()
        
        return JsonResponse({'success': True, 'message': 'File deleted successfully'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

@login_required
def reprocess_file(request, file_id):
    """Reprocess failed file"""
    file_obj = get_object_or_404(UploadedFile, id=file_id, user=request.user)
    
    if file_obj.status != 'failed':
        messages.warning(request, 'File is not in failed status')
        return redirect('textprocessor:file_detail', file_id=file_id)
    
    try:
        file_obj.status = 'processing'
        file_obj.error_message = None
        file_obj.save()
        
        process_uploaded_file(file_obj)
        messages.success(request, 'File reprocessed successfully!')
    except Exception as e:
        messages.error(request, f'Reprocessing failed: {str(e)}')
    
    return redirect('textprocessor:file_detail', file_id=file_id)

# Legacy view for compatibility
def upload_file_view(request):
    """Legacy view - redirect to new file list"""
    return redirect('textprocessor:file_list')

def file_insights(request, file_id):
    """Render summary and Q&A interface for the uploaded file"""
    file_obj = get_object_or_404(UploadedFile, id=file_id, user=request.user, status='completed')
    dashboard_template = get_dashboard_template(request.user)
    summary = ai_service.summarize_content(file_obj.extracted_text)
    return render(request, 'textprocessor/file_insights.html', {
        'file': file_obj,
        'summary': summary,
        'dashboard_template': dashboard_template
    })

@login_required
@require_http_methods(["POST"])
def file_qa_api(request, file_id):
    """Answer a question based on file content"""
    file_obj = get_object_or_404(UploadedFile, id=file_id, user=request.user, status='completed')
    question = request.POST.get('question', '').strip()
    if not question:
        return JsonResponse({'error': 'No question provided.'}, status=400)
    answer = ai_service.answer_question(file_obj.extracted_text, question)
    return JsonResponse({'answer': answer})