# AI-Powered Quiz Generator

## Overview
AI-Powered Quiz Generator is a Django-based web application that allows teachers and students to generate, manage, and take quizzes enhanced with AI capabilities. The system integrates with AI services (Google Gemini and OpenAI) to dynamically generate quiz questions and supports custom user roles, detailed dashboards, and rich templates.

## Tech Stack
- Python 3.x
- Django 5.2.3
- SQLite (default development database)
- Google Gemini API
- OpenAI API (fallback)
- `python-decouple` for environment configuration
- `requests` for HTTP requests to external AI services
- HTML/CSS/JavaScript for frontend templates

## Installation

1. Clone the repository:
   ```powershell
   git clone https://github.com/SajidKalam-byte/AI-Powered_Quiz_Generator.git
   cd AI-Powered_Quiz_Generator/quizhub
   ```
2. Create a virtual environment and install dependencies:
   ```powershell
   python -m venv env; .\env\Scripts\Activate; pip install -r requirements.txt
   ```
3. Add environment variables (e.g., `.env` file):
   ```ini
   SECRET_KEY=your-secret-key
   GEMINI_API_KEY=your-gemini-key
   OPENAI_API_KEY=your-openai-key
   ```
4. Run migrations and start server:
   ```powershell
   python manage.py migrate; python manage.py runserver
   ```
5. Access the app at `http://localhost:8000/`.

## Authentication & Authorization

- **CustomUser** model extends Django's `AbstractBaseUser` and `PermissionsMixin`.
- Roles: `student`, `teacher`, `admin`.
- `CustomUserManager` handles creation of regular users and superusers.
- Registration views:
  - `/users/student_register/`
  - `/users/teacher_register/`
- Login and logout via `/users/login/` and `/users/logout/`.
- Role-based access enforced by custom decorator (`role_required`) and middleware (`users.middleware.AuthenticationMiddleware`).
- Admin dashboard (`admin_dashboard` app) accessible only to superusers or users with `admin` role.

## API Endpoints

### AI Quiz Generation (`ai` app)
- **Test endpoint**: `GET /ai/test/`
- **Generate quiz**: `POST /ai/generate-quiz/`
  - Request JSON: `{ "topic": "...", "num_questions": 5, "difficulty": "MEDIUM", "question_types": ["MULTIPLE_CHOICE"], "content": "optional base content" }`
  - Response: JSON-formatted quiz with title, description, questions, total_points, etc.
- **Generate questions only**: `POST /ai/generate-questions/`

### Quiz Management (`quizzes` app)
- Endpoints and views under `/quizzes/` route.
- Models: `Quiz`, `UserQuizAttempt` track quiz metadata and attempts.

### Other apps
- `textprocessor`: helper services for processing content, templates, and analytics.
- `core`: shared utilities and models.
- `student`, `staff`, `admin_dashboard`: role-specific views and templates.

## Quiz Generation Flow

1. Client submits quiz generation request via `/ai/generate-quiz/`.
2. `AIQuizGenerator.generate_quiz()` attempts generation in order:
   - **Primary**: Google Gemini (`_generate_with_gemini`).
   - **Fallback**: OpenAI Chat Completion (`_generate_with_openai`).
   - **Final**: Rule-based fallback (`_generate_fallback_quiz`).
3. AI response is parsed (`_parse_ai_response`) into structured JSON (`QuizQuestion` dataclass).
4. Client receives quiz JSON and can render it in templates or store in database.

## Project Structure
```
quizhub/                  # Django project root
├── admin_dashboard/      # Admin-specific dashboards & views
├── ai/                   # AI quiz generation logic & endpoints
├── core/                 # Shared models and utilities
├── quizzes/              # Quiz models, views, and management
├── student/              # Student-specific views and templates
├── staff/                # Staff/teacher-specific views and templates
├── textprocessor/        # Content processing and analytics
├── users/                # CustomUser model, auth views, middleware
├── static/               # Global static assets (css, js, media)
├── templates/            # Global templates
├── db.sqlite3            # Development database
├── manage.py             # Django management script
└── requirements.txt      # Python dependencies
```

## Contributing

1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/YourFeature`).
3. Commit your changes and open a pull request.

---

*(This documentation was generated automatically. For further details, refer to in-code docstrings and comments.)*
