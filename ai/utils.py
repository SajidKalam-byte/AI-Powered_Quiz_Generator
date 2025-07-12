"""
Enhanced AI utilities for quiz generation and content analysis
"""
import json
import logging
import re
import hashlib
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta

import requests
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

logger = logging.getLogger(__name__)

@dataclass
class AIProvider:
    """AI Provider configuration"""
    name: str
    api_key: str
    endpoint: str
    model: str
    max_tokens: int = 4096
    temperature: float = 0.7
    timeout: int = 45

@dataclass
class ContentAnalysis:
    """Content analysis results"""
    topics: List[str]
    key_concepts: List[str]
    difficulty_level: str
    readability_score: float
    word_count: int
    estimated_reading_time: int  # minutes
    language: str
    content_type: str  # academic, professional, casual, etc.
    summary: str

@dataclass
class QuizMetrics:
    """Quiz quality metrics"""
    question_clarity: float
    option_quality: float
    difficulty_consistency: float
    topic_relevance: float
    overall_score: float

class EnhancedAIService:
    """Enhanced AI service with multiple providers and advanced features"""
    
    def __init__(self):
        self.providers = self._initialize_providers()
        self.cache_timeout = 3600  # 1 hour
        
    def _initialize_providers(self) -> Dict[str, AIProvider]:
        """Initialize available AI providers"""
        providers = {}
        
        # Google Gemini
        gemini_key = getattr(settings, 'GEMINI_API_KEY', '')
        if gemini_key:
            providers['gemini'] = AIProvider(
                name='Gemini',
                api_key=gemini_key,
                endpoint='https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent',
                model='gemini-2.0-flash',
                max_tokens=4096,
                temperature=0.7
            )
        
        # OpenAI GPT
        openai_key = getattr(settings, 'OPENAI_API_KEY', '')
        if openai_key:
            providers['openai'] = AIProvider(
                name='OpenAI',
                api_key=openai_key,
                endpoint='https://api.openai.com/v1/chat/completions',
                model='gpt-4',
                max_tokens=4096,
                temperature=0.7
            )
        
        return providers
    
    def analyze_content(self, text: str, cache_key: Optional[str] = None) -> ContentAnalysis:
        """Analyze content for educational value and characteristics"""
        if cache_key:
            cached_result = cache.get(f"content_analysis_{cache_key}")
            if cached_result:
                return ContentAnalysis(**cached_result)
        
        try:
            # Basic analysis
            word_count = len(text.split())
            estimated_reading_time = max(1, word_count // 200)  # ~200 words per minute
            
            # AI-powered analysis
            analysis_prompt = f"""
            Analyze the following educational content and provide detailed insights:
            
            Content:
            {text[:3000]}...
            
            Provide analysis in JSON format:
            {{
                "topics": ["topic1", "topic2", ...],
                "key_concepts": ["concept1", "concept2", ...],
                "difficulty_level": "EASY|MEDIUM|HARD",
                "readability_score": 0.0-100.0,
                "language": "en|es|fr|etc",
                "content_type": "academic|professional|casual|technical",
                "summary": "Brief 2-3 sentence summary"
            }}
            """
            
            ai_response = self._call_ai_provider(analysis_prompt, 'content_analysis')
            
            if ai_response:
                # Merge AI analysis with basic analysis
                ai_data = json.loads(ai_response)
                result = ContentAnalysis(
                    topics=ai_data.get('topics', []),
                    key_concepts=ai_data.get('key_concepts', []),
                    difficulty_level=ai_data.get('difficulty_level', 'MEDIUM'),
                    readability_score=ai_data.get('readability_score', 50.0),
                    word_count=word_count,
                    estimated_reading_time=estimated_reading_time,
                    language=ai_data.get('language', 'en'),
                    content_type=ai_data.get('content_type', 'academic'),
                    summary=ai_data.get('summary', 'Educational content for analysis.')
                )
            else:
                # Fallback analysis
                result = self._fallback_content_analysis(text, word_count, estimated_reading_time)
            
            # Cache result
            if cache_key:
                cache.set(f"content_analysis_{cache_key}", asdict(result), self.cache_timeout)
            
            return result
            
        except Exception as e:
            logger.error(f"Content analysis failed: {str(e)}")
            return self._fallback_content_analysis(text, word_count, estimated_reading_time)
    
    def generate_quiz_questions(self, 
                              topic: str, 
                              content: str, 
                              num_questions: int, 
                              difficulty: str,
                              question_types: List[str],
                              **kwargs) -> Dict[str, Any]:
        """Generate high-quality quiz questions with enhanced prompting"""
        
        # Create cache key
        cache_key = hashlib.md5(
            f"{topic}_{num_questions}_{difficulty}_{','.join(question_types)}_{content[:500]}".encode()
        ).hexdigest()
        
        cached_result = cache.get(f"quiz_{cache_key}")
        if cached_result:
            logger.info("Returning cached quiz result")
            return cached_result
        
        # Enhanced prompt with better instructions
        prompt = self._build_advanced_quiz_prompt(
            topic, content, num_questions, difficulty, question_types, **kwargs
        )
        
        result = None
        for provider_name in ['gemini', 'openai']:
            if provider_name in self.providers:
                try:
                    logger.info(f"Attempting quiz generation with {provider_name}")
                    ai_response = self._call_ai_provider(prompt, 'quiz_generation', provider_name)
                    
                    if ai_response:
                        result = self._parse_quiz_response(ai_response, num_questions)
                        if result:
                            # Add quality metrics
                            result['quality_metrics'] = self._calculate_quality_metrics(result)
                            break
                            
                except Exception as e:
                    logger.error(f"{provider_name} failed: {str(e)}")
                    continue
        
        if not result:
            logger.warning("All AI providers failed, using fallback")
            result = self._generate_fallback_quiz(topic, num_questions, difficulty)
        
        # Cache successful result
        if result:
            cache.set(f"quiz_{cache_key}", result, self.cache_timeout)
        
        return result
    
    def summarize_content(self, text: str) -> str:
        """Generate a concise educational summary of the provided content"""
        prompt = f"""
You are an AI assistant specialized in educational summaries.
Please provide a clear, concise summary of the following content, highlighting key points and main ideas suitable for teachers and students.

Content:
{text[:5000]}
"""
        try:
            ai_response = self._call_ai_provider(prompt, 'summarization')
            return ai_response.strip() if ai_response else 'No summary available.'
        except Exception as e:
            logger.error(f"Content summarization failed: {str(e)}")
            return 'Error generating summary.'
    
    def _build_advanced_quiz_prompt(self, 
                                  topic: str, 
                                  content: str, 
                                  num_questions: int, 
                                  difficulty: str,
                                  question_types: List[str],
                                  **kwargs) -> str:
        """Build advanced prompt for quiz generation"""
        
        category = kwargs.get('category', 'General')
        language = kwargs.get('language', 'en')
        cognitive_levels = kwargs.get('cognitive_levels', ['understand', 'apply'])
        
        # Difficulty-specific instructions
        difficulty_instructions = {
            'EASY': "Focus on basic recall, definitions, and simple recognition of concepts.",
            'MEDIUM': "Include application of concepts, analysis of relationships, and problem-solving.",
            'HARD': "Emphasize synthesis, evaluation, critical thinking, and complex problem-solving."
        }
        
        # Question type instructions
        type_instructions = {
            'MULTIPLE_CHOICE': "4 options (A, B, C, D) with one clearly correct answer and plausible distractors",
            'TRUE_FALSE': "Clear statements that are definitively true or false",
            'SHORT_ANSWER': "Questions requiring brief written responses (1-3 sentences)"
        }
        
        content_section = f"\n\nBASE CONTENT:\n{content[:4000]}" if content else ""
        
        prompt = f"""
You are an expert educational assessment creator. Generate a high-quality quiz with the following specifications:

QUIZ PARAMETERS:
- Topic: {topic}
- Category: {category}
- Questions: {num_questions}
- Difficulty: {difficulty}
- Question Types: {', '.join(question_types)}
- Language: {language}
- Cognitive Levels: {', '.join(cognitive_levels)}

DIFFICULTY LEVEL: {difficulty}
{difficulty_instructions.get(difficulty, '')}

QUESTION QUALITY REQUIREMENTS:
1. Each question must be directly related to {topic}
2. Use clear, concise language appropriate for the difficulty level
3. Avoid ambiguous wording or trick questions
4. Ensure cultural neutrality and inclusivity
5. Create realistic, plausible distractors for multiple choice
6. Include detailed explanations that teach concepts

QUESTION TYPES TO USE:
{chr(10).join([f"- {qtype}: {type_instructions.get(qtype, '')}" for qtype in question_types])}

{content_section}

IMPORTANT: Respond with ONLY valid JSON. Do not include any text before or after the JSON.

{{
    "title": "Engaging, specific quiz title",
    "description": "What students will learn from this quiz",
    "estimated_time": "X minutes",
    "learning_objectives": ["objective1", "objective2"],
    "questions": [
        {{
            "id": 1,
            "type": "MULTIPLE_CHOICE",
            "text": "Question text here",
            "options": {{"A": "Option A", "B": "Option B", "C": "Option C", "D": "Option D"}},
            "correct_option": "A",
            "explanation": "Detailed explanation with educational value",
            "difficulty": "{difficulty}",
            "cognitive_level": "understand",
            "topic_tags": ["tag1", "tag2"],
            "points": 10,
            "estimated_time": 90
        }}
    ],
    "metadata": {{
        "total_points": {num_questions * 10},
        "average_time_per_question": 90,
        "difficulty_distribution": {{"easy": 0, "medium": 0, "hard": 0}},
        "cognitive_distribution": {{"understand": {num_questions}}}
    }}
}}

Generate exactly {num_questions} questions. Ensure variety in question structure and avoid repetitive patterns.
"""
        return prompt
    
    def _call_ai_provider(self, prompt: str, task_type: str, provider_name: str = None) -> Optional[str]:
        """Call AI provider with error handling and retries"""
        if not provider_name:
            # Try providers in order of preference
            for pname in ['gemini', 'openai']:
                if pname in self.providers:
                    result = self._call_ai_provider(prompt, task_type, pname)
                    if result:
                        return result
            return None
        
        if provider_name not in self.providers:
            return None
        
        provider = self.providers[provider_name]
        
        try:
            if provider_name == 'gemini':
                return self._call_gemini(provider, prompt)
            elif provider_name == 'openai':
                return self._call_openai(provider, prompt)
        except Exception as e:
            logger.error(f"AI provider {provider_name} failed: {str(e)}")
            return None
    
    def _call_gemini(self, provider: AIProvider, prompt: str) -> Optional[str]:
        """Call Google Gemini API"""
        response = requests.post(
            provider.endpoint,
            headers={
                'Content-Type': 'application/json',
                'X-goog-api-key': provider.api_key
            },
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": provider.temperature,
                    "topK": 40,
                    "topP": 0.95,
                    "maxOutputTokens": provider.max_tokens,
                }
            },
            timeout=provider.timeout
        )
        
        if response.status_code == 200:
            return (
                response.json()
                .get('candidates', [{}])[0]
                .get('content', {})
                .get('parts', [{}])[0]
                .get('text', '')
            )
        
        return None
    
    def _call_openai(self, provider: AIProvider, prompt: str) -> Optional[str]:
        """Call OpenAI API"""
        try:
            import openai
            
            response = requests.post(
                provider.endpoint,
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {provider.api_key}'
                },
                json={
                    "model": provider.model,
                    "messages": [
                        {"role": "system", "content": "You are an expert educational content creator."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": provider.temperature,
                    "max_tokens": provider.max_tokens
                },
                timeout=provider.timeout
            )
            
            if response.status_code == 200:
                return response.json()['choices'][0]['message']['content']
        
        except ImportError:
            logger.warning("OpenAI library not installed")
        
        return None
    
    def _parse_quiz_response(self, response: str, expected_questions: int) -> Optional[Dict]:
        """Parse and validate AI quiz response with improved error handling"""
        try:
            # Clean up the response
            response = response.strip()
            
            # Try to extract JSON from various formats
            json_text = None
            
            # Method 1: Look for JSON blocks
            json_match = re.search(r'```json\s*(\{[\s\S]*?\})\s*```', response, re.DOTALL)
            if json_match:
                json_text = json_match.group(1)
            else:
                # Method 2: Look for JSON without code blocks
                json_match = re.search(r'(\{[\s\S]*?\})', response, re.DOTALL)
                if json_match:
                    json_text = json_match.group(1)
            
            if not json_text:
                logger.error("No JSON found in response")
                return None
                
            # Clean up common JSON issues
            json_text = json_text.strip()
            
            # Try to parse JSON
            try:
                quiz_data = json.loads(json_text)
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {e}")
                # Try to fix common issues
                json_text = self._fix_common_json_issues(json_text)
                quiz_data = json.loads(json_text)
            
            # Validate structure
            if not self._validate_quiz_data(quiz_data, expected_questions):
                logger.error("Quiz data validation failed")
                return None
            
            # Enhance data
            return self._enhance_quiz_data(quiz_data)
            
        except Exception as e:
            logger.error(f"Failed to parse quiz response: {str(e)}")
            logger.error(f"Response preview: {response[:500]}...")
            return None
    
    def _fix_common_json_issues(self, json_text: str) -> str:
        """Fix common JSON formatting issues"""
        # Remove trailing commas
        json_text = re.sub(r',\s*([}\]])', r'\1', json_text)
        
        # Fix unescaped quotes in strings
        json_text = re.sub(r'(?<!\\)"(?![\s]*[,}\]:])', r'\\"', json_text)
        
        # Ensure proper string quoting
        json_text = re.sub(r'([{,]\s*)([A-Za-z_][A-Za-z0-9_]*)\s*:', r'\1"\2":', json_text)
        
        return json_text
    
    def _validate_quiz_data(self, data: Dict, expected_questions: int) -> bool:
        """Validate quiz data structure and content"""
        if not isinstance(data, dict):
            return False
        
        if 'questions' not in data or not isinstance(data['questions'], list):
            return False
        
        questions = data['questions']
        if len(questions) < expected_questions * 0.7:  # Allow some flexibility
            return False
        
        for q in questions:
            if not self._validate_question(q):
                return False
        
        return True
    
    def _validate_question(self, question: Dict) -> bool:
        """Validate individual question structure"""
        required_fields = ['text', 'type', 'correct_option']
        
        if not all(field in question for field in required_fields):
            return False
        
        if question['type'] == 'MULTIPLE_CHOICE':
            if 'options' not in question:
                return False
            
            options = question['options']
            if not isinstance(options, dict) or set(options.keys()) != {'A', 'B', 'C', 'D'}:
                return False
            
            if question['correct_option'] not in ['A', 'B', 'C', 'D']:
                return False
        
        return True
    
    def _enhance_quiz_data(self, quiz_data: Dict) -> Dict:
        """Enhance quiz data with additional metadata"""
        if 'metadata' not in quiz_data:
            quiz_data['metadata'] = {}
        
        questions = quiz_data['questions']
        
        # Calculate metadata
        total_points = sum(q.get('points', 10) for q in questions)
        avg_time = sum(q.get('estimated_time', 90) for q in questions) / len(questions)
        
        # Calculate distributions
        difficulty_dist = {'easy': 0, 'medium': 0, 'hard': 0}
        cognitive_dist = {'remember': 0, 'understand': 0, 'apply': 0, 'analyze': 0, 'evaluate': 0, 'create': 0}
        
        for q in questions:
            diff = q.get('difficulty', 'MEDIUM').lower()
            if diff in difficulty_dist:
                difficulty_dist[diff] += 1
            
            cog = q.get('cognitive_level', 'understand')
            if cog in cognitive_dist:
                cognitive_dist[cog] += 1
        
        quiz_data['metadata'].update({
            'total_points': total_points,
            'average_time_per_question': int(avg_time),
            'difficulty_distribution': difficulty_dist,
            'cognitive_distribution': cognitive_dist,
            'generated_at': timezone.now().isoformat()
        })
        
        return quiz_data
    
    def _calculate_quality_metrics(self, quiz_data: Dict) -> QuizMetrics:
        """Calculate quality metrics for generated quiz"""
        questions = quiz_data.get('questions', [])
        
        if not questions:
            return QuizMetrics(0, 0, 0, 0, 0)
        
        # Simple quality scoring (can be enhanced with ML models)
        question_clarity = sum(
            min(100, len(q.get('text', ''))) / 100 for q in questions
        ) / len(questions)
        
        option_quality = sum(
            1 for q in questions 
            if q.get('type') == 'MULTIPLE_CHOICE' and 
            len(q.get('options', {})) == 4
        ) / len(questions)
        
        difficulty_consistency = 1.0  # Placeholder
        topic_relevance = 1.0  # Placeholder
        
        overall_score = (question_clarity + option_quality + difficulty_consistency + topic_relevance) / 4
        
        return QuizMetrics(
            question_clarity=question_clarity,
            option_quality=option_quality,
            difficulty_consistency=difficulty_consistency,
            topic_relevance=topic_relevance,
            overall_score=overall_score
        )
    
    def _fallback_content_analysis(self, text: str, word_count: int, reading_time: int) -> ContentAnalysis:
        """Fallback content analysis when AI fails"""
        # Basic keyword extraction
        words = re.findall(r'\b[A-Z][a-z]+\b', text)
        word_freq = {}
        for word in words:
            if len(word) > 3:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        topics = [word for word, _ in sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]]
        
        return ContentAnalysis(
            topics=topics,
            key_concepts=topics[:5],
            difficulty_level='MEDIUM',
            readability_score=50.0,
            word_count=word_count,
            estimated_reading_time=reading_time,
            language='en',
            content_type='academic',
            summary='Educational content for quiz generation.'
        )
    
    def _generate_fallback_quiz(self, topic: str, num_questions: int, difficulty: str) -> Dict:
        """Generate fallback quiz when AI fails"""
        questions = []
        
        for i in range(min(num_questions, 5)):
            question = {
                "id": i + 1,
                "type": "MULTIPLE_CHOICE",
                "text": f"Which of the following best describes {topic}?",
                "options": {
                    "A": f"Key aspect of {topic}",
                    "B": f"Related concept to {topic}",
                    "C": f"Alternative approach to {topic}",
                    "D": f"Unrelated concept"
                },
                "correct_option": "A",
                "explanation": f"This option best represents the core concepts of {topic}.",
                "difficulty": difficulty,
                "cognitive_level": "understand",
                "topic_tags": [topic.lower()],
                "points": 10,
                "estimated_time": 90
            }
            questions.append(question)
        
        return {
            "title": f"Quiz: {topic}",
            "description": f"A basic quiz covering fundamental concepts of {topic}",
            "estimated_time": f"{len(questions) * 2} minutes",
            "learning_objectives": [f"Understand basic concepts of {topic}"],
            "questions": questions,
            "metadata": {
                "total_points": len(questions) * 10,
                "average_time_per_question": 90,
                "difficulty_distribution": {difficulty.lower(): len(questions)},
                "cognitive_distribution": {"understand": len(questions)},
                "generated_at": timezone.now().isoformat(),
                "is_fallback": True
            }
        }
    
    def answer_question(self, content: str, question: str) -> str:
        """Answer a user question based on provided content"""
        prompt = f"""
You are an AI assistant specialized in educational content.
Based on the following content, answer the user's question in a clear and concise manner.

Content:
{content}

Question:
{question}
"""
        try:
            ai_response = self._call_ai_provider(prompt, 'question_answering')
            return ai_response.strip() if ai_response else "I'm sorry, I don't have an answer for that."
        except Exception as e:
            logger.error(f"Question answering failed: {str(e)}")
            return "I'm sorry, something went wrong while answering your question."

# Global instance
ai_service = EnhancedAIService()
