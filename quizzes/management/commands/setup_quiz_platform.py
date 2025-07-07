from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from quizzes.models import UserProfile, Category, Quiz, Question, DailyChallenge, Leaderboard
from django.utils import timezone
import random

User = get_user_model()

class Command(BaseCommand):
    help = 'Setup initial data for the quiz platform'

    def add_arguments(self, parser):
        parser.add_argument(
            '--create-profiles',
            action='store_true',
            help='Create user profiles for existing users',
        )
        parser.add_argument(
            '--create-sample-data',
            action='store_true',
            help='Create sample categories and quizzes',
        )
        parser.add_argument(
            '--update-leaderboards',
            action='store_true',
            help='Update all leaderboards',
        )

    def handle(self, *args, **options):
        if options['create_profiles']:
            self.create_user_profiles()
        
        if options['create_sample_data']:
            self.create_sample_data()
        
        if options['update_leaderboards']:
            self.update_leaderboards()
        
        self.stdout.write(
            self.style.SUCCESS('Setup completed successfully!')
        )

    def create_user_profiles(self):
        """Create UserProfile for all users who don't have one"""
        users_without_profile = User.objects.filter(quiz_profile__isnull=True)
        created_count = 0
        
        for user in users_without_profile:
            UserProfile.objects.create(user=user)
            created_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(f'Created {created_count} user profiles')
        )

    def create_sample_data(self):
        """Create sample categories and quizzes"""
        # Create sample categories
        sample_categories = [
            {
                'name': 'Science & Technology',
                'description': 'Explore the wonders of science and technology',
                'icon': 'bi-cpu',
                'color': 'primary'
            },
            {
                'name': 'History & Geography',
                'description': 'Journey through time and around the world',
                'icon': 'bi-globe',
                'color': 'success'
            },
            {
                'name': 'Arts & Literature',
                'description': 'Discover the beauty of arts and literature',
                'icon': 'bi-palette',
                'color': 'info'
            },
            {
                'name': 'Sports & Entertainment',
                'description': 'Test your knowledge of sports and entertainment',
                'icon': 'bi-trophy',
                'color': 'warning'
            },
            {
                'name': 'General Knowledge',
                'description': 'A mix of interesting topics and facts',
                'icon': 'bi-lightbulb',
                'color': 'secondary'
            }
        ]
        
        created_categories = 0
        for cat_data in sample_categories:
            category, created = Category.objects.get_or_create(
                name=cat_data['name'],
                defaults=cat_data
            )
            if created:
                created_categories += 1
        
        self.stdout.write(
            self.style.SUCCESS(f'Created {created_categories} categories')
        )

        # Create sample quiz if admin user exists
        admin_users = User.objects.filter(is_superuser=True)
        if admin_users.exists() and Category.objects.exists():
            self.create_sample_quiz(admin_users.first())

    def create_sample_quiz(self, creator):
        """Create a sample quiz with questions"""
        science_category = Category.objects.filter(name__icontains='science').first()
        if not science_category:
            science_category = Category.objects.first()

        quiz, created = Quiz.objects.get_or_create(
            title='Basic Science Quiz',
            defaults={
                'description': 'Test your knowledge of basic scientific concepts and principles.',
                'category': science_category,
                'created_by': creator,
                'difficulty': 'MEDIUM',
                'quiz_type': 'REGULAR',
                'time_limit': 15,
                'max_attempts': 3,
                'points_reward': 100,
                'tags': 'science, physics, chemistry, biology',
                'is_published': True
            }
        )

        if created:
            # Create sample questions
            sample_questions = [
                {
                    'text': 'What is the chemical symbol for water?',
                    'option_a': 'H2O',
                    'option_b': 'CO2',
                    'option_c': 'NaCl',
                    'option_d': 'O2',
                    'correct_option': 'A',
                    'explanation': 'Water is composed of two hydrogen atoms and one oxygen atom, hence H2O.',
                    'points': 10,
                    'order': 1
                },
                {
                    'text': 'Which planet is known as the Red Planet?',
                    'option_a': 'Venus',
                    'option_b': 'Mars',
                    'option_c': 'Jupiter',
                    'option_d': 'Saturn',
                    'correct_option': 'B',
                    'explanation': 'Mars appears red due to iron oxide (rust) on its surface.',
                    'points': 10,
                    'order': 2
                },
                {
                    'text': 'What is the speed of light in a vacuum?',
                    'option_a': '300,000 km/s',
                    'option_b': '299,792,458 m/s',
                    'option_c': '186,000 miles/s',
                    'option_d': 'All of the above',
                    'correct_option': 'D',
                    'explanation': 'All these values represent the speed of light in different units.',
                    'points': 15,
                    'order': 3
                },
                {
                    'text': 'Which gas makes up the majority of Earth\'s atmosphere?',
                    'option_a': 'Oxygen',
                    'option_b': 'Carbon Dioxide',
                    'option_c': 'Nitrogen',
                    'option_d': 'Hydrogen',
                    'correct_option': 'C',
                    'explanation': 'Nitrogen makes up about 78% of Earth\'s atmosphere.',
                    'points': 10,
                    'order': 4
                },
                {
                    'text': 'What is the smallest unit of matter?',
                    'option_a': 'Molecule',
                    'option_b': 'Atom',
                    'option_c': 'Electron',
                    'option_d': 'Proton',
                    'correct_option': 'B',
                    'explanation': 'An atom is the smallest unit of ordinary matter that forms a chemical element.',
                    'points': 10,
                    'order': 5
                }
            ]

            for question_data in sample_questions:
                Question.objects.create(quiz=quiz, **question_data)

            self.stdout.write(
                self.style.SUCCESS(f'Created sample quiz "{quiz.title}" with {len(sample_questions)} questions')
            )

    def update_leaderboards(self):
        """Update all leaderboard periods"""
        periods = ['DAILY', 'WEEKLY', 'MONTHLY', 'ALL_TIME']
        updated_count = 0
        
        for period in periods:
            try:
                Leaderboard.update_leaderboard(period)
                updated_count += 1
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f'Failed to update {period} leaderboard: {e}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'Updated {updated_count} leaderboards')
        )
