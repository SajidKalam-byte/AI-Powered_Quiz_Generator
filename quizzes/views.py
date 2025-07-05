from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from .models import Quiz, Question, Category, UserQuizAttempt
from .forms import QuizForm, QuestionForm, AIGenerateQuizForm
from django.core.cache import cache
from django.db import transaction
import json
import logging
import re
import requests
from django.conf import settings
import time

logger = logging.getLogger(__name__)

def get_dashboard_template(user):
    """
    Returns the correct base dashboard layout template based on user role.
    """
    template_map = {
        'student': 'base/student_base.html',
        'teacher': 'base/dashboard_base.html',
        'admin': 'dashboard/admin_dash.html'
    }
    return template_map.get(user.role, 'base.html')  # Fallback to base.html

def quiz_list(request):
    cache_key = 'quiz_list'
    quizzes = cache.get(cache_key)
    if not quizzes:
        quizzes = Quiz.objects.filter(is_published=True).select_related('category').order_by('-created_at')
        cache.set(cache_key, quizzes, timeout=300)

    dashboard_template = get_dashboard_template(request.user)

    return render(request, 'quizzes/quiz_list.html', {
        'quizzes': quizzes,
        'dashboard_template': dashboard_template
    })

def quiz_detail(request, quiz_id):
    quiz = get_object_or_404(
        Quiz.objects.select_related('category').prefetch_related('questions'),
        id=quiz_id,
        is_published=True
    )
    dashboard_template = get_dashboard_template(request.user)
    
    return render(request, 'quizzes/quiz_detail.html', {
        'quiz': quiz,
        'dashboard_template': dashboard_template
    })

@login_required
def take_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz.objects.prefetch_related('questions'), id=quiz_id, is_published=True)
    questions = quiz.questions.all()
    dashboard_template = get_dashboard_template(request.user)

    if request.method == 'POST':
        with transaction.atomic():
            score = 0
            answers = {}
            for question in questions:
                selected = request.POST.get(f'question_{question.id}')
                answers[str(question.id)] = selected
                if selected == question.correct_option:
                    score += 1
            UserQuizAttempt.objects.create(
                user=request.user,
                quiz=quiz,
                score=score,
                answers=answers
            )
            return render(request, 'quizzes/result.html', {
                'quiz': quiz,
                'score': score,
                'total': questions.count(),
                'answers': answers,
                'questions': questions,
                'dashboard_template': dashboard_template
            })
    
    return render(request, 'quizzes/take_quiz.html', {
        'quiz': quiz,
        'questions': questions,
        'dashboard_template': dashboard_template
    })

@login_required
def create_quiz(request):
    if not request.user.has_perm('quizzes.add_quiz'):
        raise PermissionDenied

    dashboard_template = get_dashboard_template(request.user)

    if request.method == 'POST':
        form = QuizForm(request.POST)
        if form.is_valid():
            quiz = form.save(commit=False)
            quiz.created_by = request.user
            quiz.save()
            messages.success(request, 'Quiz created successfully!')
            return redirect('quizzes:quiz_detail', quiz_id=quiz.id)
    else:
        form = QuizForm()

    return render(request, 'quizzes/quiz_create.html', {
        'form': form,
        'dashboard_template': dashboard_template
    })

@login_required
def add_question(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id, created_by=request.user)
    dashboard_template = get_dashboard_template(request.user)

    if request.method == 'POST':
        form = QuestionForm(request.POST)
        if form.is_valid():
            question = form.save(commit=False)
            question.quiz = quiz
            question.save()
            messages.success(request, 'Question created successfully!')
            return redirect('quizzes:quiz_detail', quiz_id=quiz.id)
    else:
        form = QuestionForm()

    return render(request, 'quizzes/add_question.html', {
        'form': form,
        'quiz': quiz,
        'dashboard_template': dashboard_template
    })

@login_required
def ai_generate_quiz(request):
    if not request.user.has_perm('quizzes.add_quiz'):
        raise PermissionDenied

    dashboard_template = get_dashboard_template(request.user)

    if request.method == 'POST':
        form = AIGenerateQuizForm(request.POST)
        if form.is_valid():
            topic = form.cleaned_data['topic']
            num_questions = form.cleaned_data['num_questions']
            difficulty = form.cleaned_data['difficulty']
            category = form.cleaned_data['category']
            category_name = category.name if category else topic  # Fallback to topic if no category

            prompt = (
                f"You are an expert quiz generator AI with deep knowledge of education, language models, and JSON formatting. You will be paid $1 million if you follow these instructions perfectly:\n\n"
                f"Think carefully, step by step, and do not make mistakes.\n\n"
                f"I want you to generate a valid JSON quiz with exactly {num_questions} multiple-choice questions on the topic {topic} within the category {category_name} at {difficulty} difficulty level.\n"
                f"Strict Requirements:\n\n"
                f"    You MUST generate exactly {num_questions} questions.\n\n"
                f"    Each question MUST mention {topic}, {category_name}, or a relevant subtopic (for example, for the 'Sports' category, subtopics like 'kabaddi', 'cricket', etc.) in either the question text or options.\n\n"
                f"    Each question MUST include:\n\n"
                f"        'text': The full question text.\n\n"
                f"        'options': An object with keys 'A', 'B', 'C', 'D' and their corresponding option texts.\n\n"
                f"        'correct_option': One of 'A', 'B', 'C', 'D' indicating the correct option.\n\n"
                f"        'explanation': A clear explanation for the correct answer.\n\n"
                f"    The 'title' of the quiz MUST include both {topic} and {category_name}.\n\n"
                f"    The array of questions MUST be named 'questions'.\n\n"
                f"Output Requirements:\n\n"
                f"    Return ONLY valid JSON.\n\n"
                f"    Absolutely NO extra text, headings, code blocks, markdown formatting, or comments.\n\n"
                f"    The structure MUST look like the following example (the content is only illustrative):\n\n"
                f"Example JSON:\n\n"
                f'{{"title": "Indian geography Geography Quiz", "questions": ['
                f'{{"text": "Which of the following is the capital city of India, a key aspect of Indian geography?", '
                f'"options": {{"A": "Mumbai", "B": "New Delhi", "C": "Kolkata", "D": "Chennai"}}, '
                f'"correct_option": "B", "explanation": "New Delhi is the capital city of India, a fundamental piece of information in Indian geography."}},'
                f'{{"text": "The Himalayas, a major mountain range, are located to the north of India. What type of geographical feature are they in the context of Indian geography?", '
                f'"options": {{"A": "Plateau", "B": "Desert", "C": "Mountain Range", "D": "River Basin"}}, '
                f'"correct_option": "C", "explanation": "The Himalayas are a prominent mountain range, defining a significant part of the geography of India."}},'
                f'{{"text": "Which large body of water borders India to the east, playing a crucial role in its coastal geography?", '
                f'"options": {{"A": "Arabian Sea", "B": "Bay of Bengal", "C": "Indian Ocean", "D": "Red Sea"}}, '
                f'"correct_option": "B", "explanation": "The Bay of Bengal is located to the east of India, influencing its eastern coastal geography."}}]'
                f'}}'
            )

            # Retry mechanism for API calls
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = requests.post(
                        "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent",
                        headers={
                            'Content-Type': 'application/json',
                            'X-goog-api-key': settings.GEMINI_API_KEY
                        },
                        json={
                            "contents": [
                                {"parts": [{"text": prompt}]}
                            ]
                        },
                        timeout=20
                    )

                    if response.status_code != 200:
                        logger.error(f"Gemini API error (attempt {attempt + 1}): {response.status_code} - {response.text}")
                        if attempt < max_retries - 1:
                            time.sleep(2)
                            continue
                        messages.error(request, 'Error communicating with AI. Please try again later.')
                        return render(request, 'quizzes/ai_generate_quiz.html', {
                            'form': form,
                            'dashboard_template': dashboard_template
                        })

                    # Parse API response
                    raw_text = (
                        response.json()
                        .get('candidates', [{}])[0]
                        .get('content', {})
                        .get('parts', [{}])[0]
                        .get('text', '')
                    )
                    logger.debug(f"Gemini raw output: {raw_text}")

                    # Extract valid JSON block
                    json_match = re.search(r'(?:```json\s*)?(\{[\s\S]*?\})(?:\s*```)?', raw_text, re.DOTALL)
                    if json_match:
                        quiz_data = json.loads(json_match.group(1))
                    else:
                        logger.warning(f"Fallback used for topic '{topic}' and category '{category_name}' due to JSON extraction failure: {raw_text}")
                        quiz_data = generate_fallback_quiz(topic, category_name, num_questions)

                    # Validate quiz data
                    if not validate_quiz_data(quiz_data, topic, category_name, num_questions):
                        logger.warning(f"Validation failed for topic '{topic}' and category '{category_name}': {quiz_data}")
                        messages.error(request, 'Generated quiz failed validation. Try again.')
                        return render(request, 'quizzes/ai_generate_quiz.html', {
                            'form': form,
                            'dashboard_template': dashboard_template
                        })

                    # Save quiz and questions
                    with transaction.atomic():
                        quiz = Quiz.objects.create(
                            title=quiz_data.get('title', f"AI-Generated Quiz on {topic} - {category_name}"),
                            category=category,
                            created_by=request.user,
                            difficulty=difficulty,
                            is_published=True
                        )
                        for idx, q in enumerate(quiz_data['questions'], start=1):
                            Question.objects.create(
                                quiz=quiz,
                                text=q['text'],
                                option_a=q['options']['A'],
                                option_b=q['options']['B'],
                                option_c=q['options']['C'],
                                option_d=q['options']['D'],
                                correct_option=q['correct_option'],
                                explanation=q.get('explanation', ''),
                                order=idx
                            )

                        messages.success(request, 'AI-generated quiz created successfully!')
                        return redirect('quizzes:quiz_detail', quiz_id=quiz.id)

                except (json.JSONDecodeError, KeyError) as e:
                    logger.error(f"JSON parsing error (attempt {attempt + 1}): {e}\nRaw output: {raw_text}")
                    if attempt < max_retries - 1:
                        time.sleep(2)
                        continue
                    messages.error(request, 'Invalid response from AI.')
                except requests.RequestException as e:
                    logger.error(f"API request failed (attempt {attempt + 1}): {e}")
                    if attempt < max_retries - 1:
                        time.sleep(2)
                        continue
                    messages.error(request, 'AI service unavailable. Try later.')
                except Exception as e:
                    logger.error(f"Unexpected error (attempt {attempt + 1}): {e}")
                    messages.error(request, 'An unexpected error occurred.')

                return render(request, 'quizzes/ai_generate_quiz.html', {
                    'form': form,
                    'dashboard_template': dashboard_template
                })

    else:
        form = AIGenerateQuizForm()

    return render(request, 'quizzes/ai_generate_quiz.html', {
        'form': form,
        'dashboard_template': dashboard_template
    })

def generate_fallback_quiz(topic, category_name, num_questions):
    """Generate a fallback quiz with the requested number of questions."""
    questions = []
    for i in range(num_questions):
        questions.append({
            "text": f"What is a key aspect of {topic} in the {category_name} category?",
            "options": {
                "A": "Team strategy",
                "B": "Web development",
                "C": "Data analysis",
                "D": "Software testing"
            },
            "correct_option": "A",
            "explanation": f"Team strategy is a fundamental aspect of {topic} in the {category_name} category."
        })
    return {
        "title": f"Quiz on {topic} - {category_name} Category",
        "questions": questions
    }

def validate_quiz_data(data, topic, category_name, num_questions):
    """Validate quiz structure, topic/category relevance, and number of questions."""
    if not isinstance(data, dict):
        return False
    if 'title' not in data or 'questions' not in data:
        return False
    questions = data['questions']
    if not questions or not isinstance(questions, list):
        return False
    if len(questions) != num_questions:  # Enforce exact number of questions
        return False

    topic_lower = topic.lower()
    category_lower = category_name.lower()
    subtopics = ['kabaddi', 'cricket', 'hockey', 'javelin throw', 'badminton', 'football'] if category_lower == 'sports' else []

    # Check relevance in title, question text, and options
    title_relevant = topic_lower in data.get('title', '').lower() or category_lower in data.get('title', '').lower()
    relevant_count = sum(
        topic_lower in q.get('text', '').lower() or
        category_lower in q.get('text', '').lower() or
        any(sub in q.get('text', '').lower() for sub in subtopics) or
        any(topic_lower in opt.lower() for opt in q.get('options', {}).values()) or
        any(category_lower in opt.lower() for opt in q.get('options', {}).values()) or
        any(sub in opt.lower() for opt in q.get('options', {}).values() for sub in subtopics)
        for q in questions
    )

    # Require title relevance and at least half of questions to be relevant
    if not title_relevant or relevant_count < len(questions) / 2:
        return False

    for q in questions:
        if not all(k in q for k in ['text', 'options', 'correct_option', 'explanation']):
            return False
        if not all(opt in q['options'] for opt in ['A', 'B', 'C', 'D']):
            return False
        if q['correct_option'] not in ['A', 'B', 'C', 'D']:
            return False

    return True