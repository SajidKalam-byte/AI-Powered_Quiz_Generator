from django import forms
from .models import Quiz, Question, Category

class QuizForm(forms.ModelForm):
    class Meta:
        model = Quiz
        fields = [
            'title', 'description', 'category', 'difficulty', 'quiz_type', 
            'time_limit', 'max_attempts', 'points_reward', 'tags', 'is_published'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter quiz title'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Brief description of the quiz...'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select'
            }),
            'difficulty': forms.Select(attrs={
                'class': 'form-select'
            }),
            'quiz_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'time_limit': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 5,
                'max': 180,
                'placeholder': 'Minutes'
            }),
            'max_attempts': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 10,
                'placeholder': 'Number of attempts'
            }),
            'points_reward': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 10,
                'max': 1000,
                'placeholder': 'Points'
            }),
            'tags': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter tags separated by commas'
            }),
            'is_published': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'role': 'switch'
            }),
        }

class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = [
            'question_type', 'text', 'option_a', 'option_b', 'option_c', 'option_d', 
            'correct_option', 'correct_answer', 'explanation', 'points', 'difficulty', 'order'
        ]
        widgets = {
            'question_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'text': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Enter the question text...'
            }),
            'option_a': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Option A'
            }),
            'option_b': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Option B'
            }),
            'option_c': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Option C'
            }),
            'option_d': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Option D'
            }),
            'correct_option': forms.Select(attrs={
                'class': 'form-select'
            }),
            'correct_answer': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Correct answer for short answer questions'
            }),
            'explanation': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Explanation (optional)'
            }),
            'points': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 100,
                'value': 10
            }),
            'difficulty': forms.Select(attrs={
                'class': 'form-select'
            }),
            'order': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1
            })
        }

class AIGenerateQuizForm(forms.Form):
    num_questions = forms.IntegerField(
        label="Number of Questions",
        min_value=5,
        max_value=50,
        initial=10,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Number of questions to generate'
        })
    )
    
    difficulty = forms.ChoiceField(
        label="Difficulty Level",
        choices=[
            ('EASY', 'Easy'),
            ('MEDIUM', 'Medium'),
            ('HARD', 'Hard')
        ],
        initial='MEDIUM',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    quiz_title = forms.CharField(
        label="Quiz Title",
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Leave empty for auto-generated title'
        })
    )
    
    category = forms.ModelChoiceField(
        label="Category",
        queryset=Category.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
