#!/usr/bin/env python
"""
Test script to verify AI functionality and Gemini API key
"""

from django.conf import settings
from ai.utils import ai_service
import json

print("=== Testing AI Quiz Generation ===")

# Check if Gemini API key is configured
gemini_key = getattr(settings, 'GEMINI_API_KEY', '')
print(f"Gemini API Key configured: {'Yes' if gemini_key else 'No'}")

if gemini_key:
    print(f"API Key (first 10 chars): {gemini_key[:10]}...")
    
    # Test AI service initialization
    print(f"Available providers: {list(ai_service.providers.keys())}")
    
    # Test simple quiz generation
    print("\n=== Testing Quiz Generation ===")
    
    try:
        quiz_result = ai_service.generate_quiz_questions(
            topic="Python Programming",
            content="Python is a high-level programming language known for its simplicity and readability. It supports multiple programming paradigms including object-oriented, functional, and procedural programming.",
            num_questions=2,
            difficulty="MEDIUM",
            question_types=["MULTIPLE_CHOICE"],
            category="Programming"
        )
        
        if quiz_result:
            print("✓ Quiz generation successful!")
            print(f"Quiz title: {quiz_result.get('title', 'N/A')}")
            print(f"Number of questions: {len(quiz_result.get('questions', []))}")
            
            # Show first question
            questions = quiz_result.get('questions', [])
            if questions:
                q = questions[0]
                print(f"\nFirst question:")
                print(f"Text: {q.get('text', 'N/A')}")
                print(f"Options: {q.get('options', {})}")
                print(f"Correct: {q.get('correct_option', 'N/A')}")
        else:
            print("✗ Quiz generation failed")
            
    except Exception as e:
        print(f"✗ Error during quiz generation: {e}")
        
else:
    print("✗ Gemini API key not configured")
    print("Please set GEMINI_API_KEY in your .env file")

print("\n=== Testing Direct API Call ===")
if gemini_key:
    import requests
    
    test_prompt = "Generate a simple multiple choice question about Python programming."
    
    try:
        response = requests.post(
            "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent",
            headers={
                'Content-Type': 'application/json',
                'X-goog-api-key': gemini_key
            },
            json={
                "contents": [{"parts": [{"text": test_prompt}]}],
                "generationConfig": {
                    "temperature": 0.7,
                    "topK": 40,
                    "topP": 0.95,
                    "maxOutputTokens": 1000,
                }
            },
            timeout=30
        )
        
        print(f"API Response Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✓ Direct API call successful!")
            result = response.json()
            text = (
                result.get('candidates', [{}])[0]
                .get('content', {})
                .get('parts', [{}])[0]
                .get('text', '')
            )
            print(f"Response preview: {text[:200]}...")
        else:
            print(f"✗ API call failed: {response.text}")
            
    except Exception as e:
        print(f"✗ Direct API call error: {e}")
        
print("\n=== Summary ===")
print("If you see success messages above, the AI integration is working correctly.")
print("If there are errors, check your GEMINI_API_KEY in the .env file.")
