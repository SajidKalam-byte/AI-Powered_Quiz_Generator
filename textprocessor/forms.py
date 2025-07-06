from django import forms
from .models import UploadedFile
from quizzes.models import Category

class FileUploadForm(forms.ModelForm):
    file = forms.FileField(
        label='Upload Syllabus or Educational Content',
        help_text='Supported formats: PDF, TXT, DOCX, PPTX (Max size: 10MB)',
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,.txt,.docx,.pptx',
            'multiple': False
        })
    )
    
    description = forms.CharField(
        max_length=500,
        required=False,
        label='Description (Optional)',
        help_text='Brief description of the content',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'e.g., Computer Science syllabus for semester 1...'
        })
    )
    
    class Meta:
        model = UploadedFile
        fields = ['file']
        
    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            # Check file size (10MB limit)
            if file.size > 10 * 1024 * 1024:
                raise forms.ValidationError('File size cannot exceed 10MB.')
            
            # Check file extension
            allowed_extensions = ['.pdf', '.txt', '.docx', '.pptx']
            import os
            ext = os.path.splitext(file.name)[1].lower()
            if ext not in allowed_extensions:
                raise forms.ValidationError(f'Unsupported file type. Allowed: {", ".join(allowed_extensions)}')
        
        return file


class QuizFromFileForm(forms.Form):
    """Form to generate quiz from uploaded file"""
    uploaded_file = forms.ModelChoiceField(
        queryset=None,  # Will be set in view
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Select Uploaded File'
    )
    
    topic_selection = forms.ChoiceField(
        choices=[
            ('full_document', 'Entire Document'),
            ('specific_topic', 'Specific Topic/Section'),
            ('auto_summary', 'Auto-Generated Summary'),
        ],
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label='Quiz Content Source',
        initial='full_document'
    )
    
    specific_topic = forms.CharField(
        max_length=200,
        required=False,
        label='Specific Topic (if selected above)',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter specific topic or chapter name...'
        }),
        help_text='Only needed if you selected "Specific Topic/Section"'
    )
    
    num_questions = forms.IntegerField(
        min_value=1,
        max_value=50,
        initial=10,
        label='Number of Questions',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '10'
        })
    )
    
    difficulty = forms.ChoiceField(
        choices=[
            ('EASY', 'Easy'),
            ('MEDIUM', 'Medium'),
            ('HARD', 'Hard'),
        ],
        initial='MEDIUM',
        label='Difficulty Level',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        empty_label='Auto-detect category',
        required=False,
        label='Quiz Category',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    def __init__(self, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            # Only show user's uploaded files that have been processed
            self.fields['uploaded_file'].queryset = UploadedFile.objects.filter(
                user=user,
                status='completed',
                extracted_text__isnull=False
            )
    
    def clean(self):
        cleaned_data = super().clean()
        topic_selection = cleaned_data.get('topic_selection')
        specific_topic = cleaned_data.get('specific_topic')
        
        if topic_selection == 'specific_topic' and not specific_topic:
            raise forms.ValidationError('Please specify the topic when "Specific Topic/Section" is selected.')
        
        return cleaned_data