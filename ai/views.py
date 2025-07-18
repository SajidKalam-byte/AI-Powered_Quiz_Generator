import json
import logging
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

import requests
from django.shortcuts import render
from django.http import JsonResponse
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.core.cache import cache

logger = logging.getLogger(__name__)

def get_dashboard_template(user):
    """Returns the correct base dashboard layout template based on user role."""
    # Use the same modern template for all users to ensure consistent UI
    return 'base/student_base.html'


@dataclass
class QuizQuestion:
    """Structured quiz question data"""
    text: str
    options: Dict[str, str]
    correct_option: str
    explanation: str
    difficulty: str
    topic: str
    points: int = 10

@dataclass
class QuizGenerationRequest:
    """Request parameters for quiz generation"""
    topic: str
    num_questions: int
    difficulty: str
    question_types: List[str]
    content: Optional[str] = None
    category: Optional[str] = None
    language: str = "en"

class AIChatBot:
    """AI Chat Bot for educational and sports questions"""
    
    def __init__(self):
        self.gemini_api_key = getattr(settings, 'GEMINI_API_KEY', '')
        
    def get_chat_response(self, user_message: str, chat_history: List[Dict] = None) -> Dict[str, Any]:
        """Get AI response for chat message"""
        try:
            if not self.gemini_api_key:
                return {
                    'success': False,
                    'message': 'AI service is not configured. Please check API key settings.',
                    'response': 'Sorry, I cannot respond right now. Please try again later.'
                }
            
            # Build conversation context
            context = self._build_chat_context(user_message, chat_history)
            
            response = requests.post(
                "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent",
                headers={
                    'Content-Type': 'application/json',
                    'X-goog-api-key': self.gemini_api_key
                },
                json={
                    "contents": [{"parts": [{"text": context}]}],
                    "generationConfig": {
                        "temperature": 0.8,
                        "topK": 40,
                        "topP": 0.95,
                        "maxOutputTokens": 1024,
                    }
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if 'candidates' in result and len(result['candidates']) > 0:
                    ai_response = result['candidates'][0]['content']['parts'][0]['text']
                    return {
                        'success': True,
                        'response': ai_response.strip(),
                        'timestamp': datetime.now().isoformat()
                    }
                else:
                    return {
                        'success': False,
                        'response': 'Sorry, I could not generate a response. Please try again.'
                    }
            else:
                logger.error(f"Gemini API error: {response.status_code} - {response.text}")
                return {
                    'success': False,
                    'response': 'Sorry, I am experiencing technical difficulties. Please try again later.'
                }
                
        except requests.exceptions.Timeout:
            return {
                'success': False,
                'response': 'Request timed out. Please try again.'
            }
        except Exception as e:
            logger.error(f"Chat error: {str(e)}")
            return {
                'success': False,
                'response': 'Sorry, something went wrong. Please try again.'
            }
    
    def _build_chat_context(self, user_message: str, chat_history: List[Dict] = None) -> str:
        """Build context for chat conversation"""
        
        # System instructions
        system_prompt = """You are an AI assistant specialized in education and sports. Your role is to:

1. Answer questions about educational topics (math, science, history, literature, etc.)
2. Provide information about sports, athletes, rules, and sporting events
3. Give study tips and learning strategies
4. Explain complex concepts in simple terms
5. Provide motivational support for learning

Guidelines:
- Keep responses concise but informative
- Use simple, clear language
- Provide both short and detailed answers when appropriate
- Be encouraging and supportive
- If asked about topics outside education/sports, politely redirect to your specialty areas
- For educational content, provide examples when helpful
- For sports content, include relevant facts and context

Response format:
- For quick questions: Give a brief, direct answer
- For complex topics: Provide a structured explanation
- Always be friendly and encouraging"""

        # Add conversation history if available
        conversation_context = ""
        if chat_history:
            conversation_context = "\n\nConversation History:\n"
            for msg in chat_history[-5:]:  # Last 5 messages for context
                role = "User" if msg.get('sender') == 'user' else "Assistant"
                conversation_context += f"{role}: {msg.get('message', '')}\n"
        
        # Current user message
        current_context = f"{conversation_context}\n\nCurrent User Question: {user_message}\n\nResponse:"
        
        return system_prompt + current_context

class AIQuizGenerator:
    """Enhanced AI Quiz Generator with multiple providers and fallbacks"""
    
    def __init__(self):
        self.gemini_api_key = getattr(settings, 'GEMINI_API_KEY', '')
        self.openai_api_key = getattr(settings, 'OPENAI_API_KEY', '')
        self.current_provider = 'gemini'
        
    def generate_quiz(self, request: QuizGenerationRequest) -> Dict[str, Any]:
        """Generate quiz using available AI providers with fallbacks"""
        try:
            # Try primary provider (Gemini)
            if self.gemini_api_key:
                result = self._generate_with_gemini(request)
                if result:
                    return result
            
            # Fallback to OpenAI if available
            if self.openai_api_key:
                logger.info("Falling back to OpenAI for quiz generation")
                result = self._generate_with_openai(request)
                if result:
                    return result
            
            # Final fallback to rule-based generation
            logger.warning("Using rule-based fallback for quiz generation")
            return self._generate_fallback_quiz(request)
            
        except Exception as e:
            logger.error(f"Quiz generation failed: {str(e)}")
            return self._generate_fallback_quiz(request)
    
    def _generate_with_gemini(self, request: QuizGenerationRequest) -> Optional[Dict[str, Any]]:
        """Generate quiz using Google Gemini"""
        prompt = self._build_comprehensive_prompt(request)
        
        try:
            response = requests.post(
                "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent",
                headers={
                    'Content-Type': 'application/json',
                    'X-goog-api-key': self.gemini_api_key
                },
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {
                        "temperature": 0.7,
                        "topK": 40,
                        "topP": 0.95,
                        "maxOutputTokens": 4096,
                    }
                },
                timeout=45
            )
            
            if response.status_code == 200:
                raw_text = (
                    response.json()
                    .get('candidates', [{}])[0]
                    .get('content', {})
                    .get('parts', [{}])[0]
                    .get('text', '')
                )
                
                return self._parse_ai_response(raw_text, request)
                
        except Exception as e:
            logger.error(f"Gemini API error: {str(e)}")
            return None
    
    def _generate_with_openai(self, request: QuizGenerationRequest) -> Optional[Dict[str, Any]]:
        """Generate quiz using OpenAI"""
        try:
            import openai
            openai.api_key = self.openai_api_key
            
            prompt = self._build_comprehensive_prompt(request)
            
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert educational content creator specializing in quiz generation."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=4096
            )
            
            raw_text = response.choices[0].message.content
            return self._parse_ai_response(raw_text, request)
            
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            return None
    
    def _build_comprehensive_prompt(self, request: QuizGenerationRequest) -> str:
        """Build comprehensive prompt for AI quiz generation"""
        
        question_types_text = ", ".join(request.question_types)
        content_section = f"\n\nBase your questions on this content:\n{request.content}" if request.content else ""
        
        prompt = f"""
Create a high-quality educational quiz with the following specifications:

QUIZ REQUIREMENTS:
- Topic: {request.topic}
- Number of questions: {request.num_questions}
- Difficulty level: {request.difficulty}
- Question types: {question_types_text}
- Category: {request.category or 'General'}
- Language: {request.language}

DIFFICULTY GUIDELINES:
- EASY: Basic recall, definitions, simple concepts
- MEDIUM: Application, analysis, connecting concepts
- HARD: Synthesis, evaluation, complex problem-solving

QUESTION QUALITY STANDARDS:
1. Questions must be clear, unambiguous, and grammatically correct
2. All options should be plausible but only one clearly correct
3. Avoid trick questions or unnecessarily complex language
4. Include diverse cognitive levels (remember, understand, apply, analyze)
5. Provide detailed, educational explanations for correct answers

{content_section}

OUTPUT FORMAT - Return ONLY valid JSON:
{{
    "title": "Engaging quiz title that reflects topic and difficulty",
    "description": "Brief description of what the quiz covers",
    "estimated_time": "Estimated completion time in minutes",
    "questions": [
        {{
            "id": 1,
            "type": "MULTIPLE_CHOICE",
            "text": "Clear, specific question text",
            "options": {{
                "A": "Option A text",
                "B": "Option B text", 
                "C": "Option C text",
                "D": "Option D text"
            }},
            "correct_option": "A",
            "explanation": "Detailed explanation of why this answer is correct and why others are wrong",
            "difficulty": "{request.difficulty}",
            "topic": "{request.topic}",
            "cognitive_level": "remember|understand|apply|analyze|evaluate|create",
            "points": 10
        }}
    ],
    "total_points": {request.num_questions * 10},
    "tags": ["relevant", "tags", "for", "categorization"]
}}

IMPORTANT: Ensure all {request.num_questions} questions are relevant to {request.topic} and maintain consistent {request.difficulty} difficulty.
"""
        return prompt
    
    def _parse_ai_response(self, raw_text: str, request: QuizGenerationRequest) -> Optional[Dict[str, Any]]:
        """Parse and validate AI response"""
        try:
            # Extract JSON from response (handle markdown code blocks)
            json_match = re.search(r'(?:```json\s*)?(\{[\s\S]*?\})(?:\s*```)?', raw_text, re.DOTALL)
            if not json_match:
                raise ValueError("No valid JSON found in AI response")
            
            quiz_data = json.loads(json_match.group(1))
            
            # Validate structure
            if not self._validate_quiz_structure(quiz_data, request):
                raise ValueError("Invalid quiz structure")
            
            # Enhance quiz data
            quiz_data = self._enhance_quiz_data(quiz_data, request)
            
            return quiz_data
            
        except Exception as e:
            logger.error(f"Failed to parse AI response: {str(e)}")
            return None
    
    def _validate_quiz_structure(self, quiz_data: Dict, request: QuizGenerationRequest) -> bool:
        """Validate the structure of AI-generated quiz"""
        required_fields = ['title', 'questions']
        if not all(field in quiz_data for field in required_fields):
            return False
        
        questions = quiz_data.get('questions', [])
        if len(questions) != request.num_questions:
            logger.warning(f"Expected {request.num_questions} questions, got {len(questions)}")
            # Allow some flexibility in question count
            if len(questions) < request.num_questions * 0.7:
                return False
        
        # Validate each question
        for q in questions:
            required_q_fields = ['text', 'options', 'correct_option']
            if not all(field in q for field in required_q_fields):
                return False
            
            if not isinstance(q['options'], dict) or set(q['options'].keys()) != {'A', 'B', 'C', 'D'}:
                return False
            
            if q['correct_option'] not in ['A', 'B', 'C', 'D']:
                return False
        
        return True
    
    def _enhance_quiz_data(self, quiz_data: Dict, request: QuizGenerationRequest) -> Dict:
        """Enhance quiz data with additional metadata"""
        # Add missing fields
        if 'description' not in quiz_data:
            quiz_data['description'] = f"A {request.difficulty.lower()} level quiz on {request.topic}"
        
        if 'estimated_time' not in quiz_data:
            # Estimate 1-2 minutes per question based on difficulty
            time_per_question = {'EASY': 1, 'MEDIUM': 1.5, 'HARD': 2}
            estimated_minutes = int(len(quiz_data['questions']) * time_per_question.get(request.difficulty, 1.5))
            quiz_data['estimated_time'] = f"{estimated_minutes} minutes"
        
        if 'total_points' not in quiz_data:
            quiz_data['total_points'] = len(quiz_data['questions']) * 10
        
        if 'tags' not in quiz_data:
            quiz_data['tags'] = [request.topic.lower(), request.difficulty.lower()]
            if request.category:
                quiz_data['tags'].append(request.category.lower())
        
        # Enhance individual questions
        for i, question in enumerate(quiz_data['questions'], 1):
            if 'id' not in question:
                question['id'] = i
            if 'difficulty' not in question:
                question['difficulty'] = request.difficulty
            if 'topic' not in question:
                question['topic'] = request.topic
            if 'points' not in question:
                question['points'] = 10
            if 'cognitive_level' not in question:
                question['cognitive_level'] = self._determine_cognitive_level(question['text'])
        
        return quiz_data
    
    def _determine_cognitive_level(self, question_text: str) -> str:
        """Determine cognitive level based on question text"""
        question_lower = question_text.lower()
        
        if any(word in question_lower for word in ['define', 'what is', 'identify', 'list', 'name']):
            return 'remember'
        elif any(word in question_lower for word in ['explain', 'describe', 'summarize', 'compare']):
            return 'understand'
        elif any(word in question_lower for word in ['apply', 'solve', 'calculate', 'demonstrate']):
            return 'apply'
        elif any(word in question_lower for word in ['analyze', 'examine', 'investigate', 'distinguish']):
            return 'analyze'
        elif any(word in question_lower for word in ['evaluate', 'assess', 'critique', 'judge']):
            return 'evaluate'
        elif any(word in question_lower for word in ['create', 'design', 'develop', 'construct']):
            return 'create'
        else:
            return 'understand'  # Default
    
    def _generate_fallback_quiz(self, request: QuizGenerationRequest) -> Dict[str, Any]:
        """Generate basic fallback quiz when AI fails"""
        questions = []
        
        # Generate basic questions based on topic
        for i in range(min(request.num_questions, 5)):
            question = {
                "id": i + 1,
                "type": "MULTIPLE_CHOICE",
                "text": f"Which of the following is most relevant to {request.topic}?",
                "options": {
                    "A": f"Primary concept of {request.topic}",
                    "B": f"Secondary aspect of {request.topic}",
                    "C": f"Related field to {request.topic}",
                    "D": f"Unrelated concept"
                },
                "correct_option": "A",
                "explanation": f"This option best represents the core concepts of {request.topic}.",
                "difficulty": request.difficulty,
                "topic": request.topic,
                "cognitive_level": "remember",
                "points": 10
            }
            questions.append(question)
        
        return {
            "title": f"Basic Quiz: {request.topic}",
            "description": f"A fundamental quiz covering {request.topic}",
            "estimated_time": "5 minutes",
            "questions": questions,
            "total_points": len(questions) * 10,
            "tags": [request.topic.lower(), "basic"]
        }

# Initialize the AI generator
ai_generator = AIQuizGenerator()

@login_required
def ai_test(request):
    """AI test page for development"""
    context = {
        'message': 'Enhanced AI Quiz Generator Test Page',
        'providers': ['Gemini', 'OpenAI', 'Fallback'],
        'current_provider': ai_generator.current_provider
    }
    return render(request, 'ai/test.html', context)

@login_required
@require_http_methods(["POST"])
def generate_quiz_questions(request):
    """Generate quiz questions using AI"""
    try:
        data = json.loads(request.body)
        
        # Create generation request
        generation_request = QuizGenerationRequest(
            topic=data.get('topic', '').strip(),
            num_questions=int(data.get('num_questions', 5)),
            difficulty=data.get('difficulty', 'MEDIUM').upper(),
            question_types=data.get('question_types', ['MULTIPLE_CHOICE']),
            content=data.get('content', ''),
            category=data.get('category', ''),
            language=data.get('language', 'en')
        )
        
        # Validate request
        if not generation_request.topic:
            return JsonResponse({'error': 'Topic is required'}, status=400)
        
        if generation_request.num_questions < 1 or generation_request.num_questions > 50:
            return JsonResponse({'error': 'Number of questions must be between 1 and 50'}, status=400)
        
        # Generate quiz
        quiz_data = ai_generator.generate_quiz(generation_request)
        
        if quiz_data:
            return JsonResponse({
                'success': True,
                'quiz': quiz_data,
                'provider': ai_generator.current_provider
            })
        else:
            return JsonResponse({'error': 'Failed to generate quiz'}, status=500)
            
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        logger.error(f"Quiz generation error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def generate_quiz(request):
    """Legacy endpoint for backward compatibility"""
    if request.method == 'GET':
        # Generate a simple test question
        quiz_data = ai_generator.generate_quiz(QuizGenerationRequest(
            topic="General Knowledge",
            num_questions=1,
            difficulty="MEDIUM",
            question_types=["MULTIPLE_CHOICE"]
        ))
        
        if quiz_data and quiz_data.get('questions'):
            return JsonResponse({'quiz': quiz_data['questions'][0]['text']})
        else:
            return JsonResponse({'error': 'Failed to generate quiz question'}, status=500)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)


def discussion(request):
    """Discussion page for AI features"""
    context = {
        'message': 'AI Discussion Page',
        'features': [
            'Multi-provider support (Gemini, OpenAI)',
            'Fallback to rule-based generation',
            'Enhanced question quality standards',
            'Cognitive level analysis'
        ],
        'dashboard_template': get_dashboard_template(request.user) if request.user.is_authenticated else 'base/auth_base.html'
    }
    return render(request, 'ai/discussion.html', context)


# Initialize chat bot
chat_bot = AIChatBot()

@login_required
@require_http_methods(["POST"])
def chat_message(request):
    """Handle chat messages and return AI responses"""
    try:
        data = json.loads(request.body)
        user_message = data.get('message', '').strip()
        
        logger.info(f"Chat message received: {user_message[:50]}...")
        
        if not user_message:
            return JsonResponse({
                'success': False,
                'error': 'Message cannot be empty'
            }, status=400)
        
        # Get chat history from session if available
        chat_history = request.session.get('chat_history', [])
        
        # Get AI response
        response = chat_bot.get_chat_response(user_message, chat_history)
        
        if response['success']:
            # Add to chat history
            chat_history.append({
                'sender': 'user',
                'message': user_message,
                'timestamp': datetime.now().isoformat()
            })
            
            chat_history.append({
                'sender': 'ai',
                'message': response['response'],
                'timestamp': response['timestamp']
            })
            
            # Keep only last 20 messages in history
            if len(chat_history) > 20:
                chat_history = chat_history[-20:]
            
            # Store in session
            request.session['chat_history'] = chat_history
            
            logger.info(f"Chat response sent successfully")
            
            return JsonResponse({
                'success': True,
                'response': response['response'],
                'timestamp': response['timestamp']
            })
        else:
            logger.error(f"Chat response failed: {response.get('message', 'Unknown error')}")
            return JsonResponse({
                'success': False,
                'error': response.get('message', 'Failed to get response'),
                'response': response['response']
            }, status=500)
            
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        logger.error(f"Chat message error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Internal server error'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def clear_chat_history(request):
    """Clear chat history"""
    try:
        request.session['chat_history'] = []
        logger.info("Chat history cleared successfully")
        return JsonResponse({
            'success': True,
            'message': 'Chat history cleared'
        })
    except Exception as e:
        logger.error(f"Clear chat history error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to clear chat history'
        }, status=500)


@login_required
@require_http_methods(["GET"])
def get_chat_history(request):
    """Get chat history"""
    try:
        chat_history = request.session.get('chat_history', [])
        return JsonResponse({
            'success': True,
            'history': chat_history
        })
    except Exception as e:
        logger.error(f"Get chat history error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to get chat history'
        }, status=500)