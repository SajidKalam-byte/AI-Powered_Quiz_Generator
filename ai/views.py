# import requests
# from django.shortcuts import render
# from django.http import JsonResponse

# from quizhub.quizhub.settings import GEMINI_API_KEY



# def ai_test(request):
#     """
#     A simple view to render the AI test page.
#     """
#     context = {
#         'message': 'AI Test Page'
#     }
#     return render(request, 'ai/test.html', context)

# def generate_quiz(request):
#     """
#     Generates a quiz question using Gemini API and returns it as JSON.
#     """
#     if request.method == 'GET':
#         url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
        
#         headers = {
#             'Content-Type': 'application/json',
#             'X-goog-api-key': GEMINI_API_KEY
#         }
        
#         data = {
#             "contents": [
#                 {
#                     "parts": [
#                         {
#                             "text": "Generate a multiple-choice quiz question about general knowledge."
#                         }
#                     ]
#                 }
#             ]
#         }
        
#         response = requests.post(url, headers=headers, json=data)
        
#         if response.status_code == 200:
#             result = response.json()
#             # Gemini response format can vary; you may need to adjust this extraction
#             ai_text = result.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', 'No content')
#             return JsonResponse({'quiz': ai_text})
#         else:
#             return JsonResponse({'error': 'Failed to get response from AI'}, status=500)
