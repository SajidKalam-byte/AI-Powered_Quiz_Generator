from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import FileUploadForm
from .models import UploadedFile
from .utils import extract_text_from_file
from django.conf import settings
import os

@login_required
def upload_file(request):
    if request.method == 'POST':
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = request.FILES['file']
            file_type = 'pdf' if uploaded_file.name.endswith('.pdf') else 'txt'
            
            # Save the file to the model
            instance = UploadedFile(
                user=request.user,
                file=uploaded_file,
                file_type=file_type
            )
            instance.save()
            
            # Extract text
            file_path = os.path.join(settings.MEDIA_ROOT, instance.file.name)
            extracted_text = extract_text_from_file(file_path, file_type)
            instance.extracted_text = extracted_text
            instance.save()
            
            return render(request, 'textprocessor/extracted_text.html', {
                'form': form,
                'extracted_text': extracted_text,
                'file': instance
            })
    else:
        form = FileUploadForm()
    
    return render(request, 'textprocessor/upload.html', {'form': form})


def upload_file_view(request):
    content = UploadedFile.objects.filter(user=request.user).order_by('-uploaded_at')
    if not content:
        return render(request, 'textprocessor/upload_view.html', {'message': 'No files uploaded yet.'})
    context = {
        'content': content,
    }
    return render(request, 'textprocessor/upload_view.html' , context)