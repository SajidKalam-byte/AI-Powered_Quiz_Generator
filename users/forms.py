from django import forms
from django.contrib.auth import get_user_model

class ProfileForm(forms.ModelForm):
    """Form for editing user profile"""
    class Meta:
        model = get_user_model()
        fields = ['full_name', 'email']
