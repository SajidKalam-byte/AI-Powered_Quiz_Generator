import PyPDF2
import os

def extract_text_from_file(file_path, file_type):
    try:
        if file_type == 'pdf':
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ''
                for page in reader.pages:
                    text += page.extract_text() or ''
                return text
        elif file_type == 'txt':
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        else:
            return ''
    except Exception as e:
        return f"Error extracting text: {str(e)}"