# Generated by Django 5.2.3 on 2025-07-06 17:56

import datetime
import django.core.validators
import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quizzes', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='DailyChallenge',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(unique=True)),
                ('bonus_points', models.PositiveIntegerField(default=50)),
                ('is_active', models.BooleanField(default=True)),
                ('participants_count', models.PositiveIntegerField(default=0)),
            ],
            options={
                'ordering': ['-date'],
            },
        ),
        migrations.CreateModel(
            name='Leaderboard',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('period', models.CharField(choices=[('DAILY', 'Daily'), ('WEEKLY', 'Weekly'), ('MONTHLY', 'Monthly'), ('ALL_TIME', 'All Time')], max_length=20)),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('top_users', models.JSONField(default=list)),
                ('last_updated', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['-last_updated'],
            },
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('total_points', models.PositiveIntegerField(default=0)),
                ('total_quizzes_completed', models.PositiveIntegerField(default=0)),
                ('current_streak', models.PositiveIntegerField(default=0)),
                ('longest_streak', models.PositiveIntegerField(default=0)),
                ('last_quiz_date', models.DateField(blank=True, null=True)),
                ('rank', models.PositiveIntegerField(default=0)),
                ('level', models.PositiveIntegerField(default=1)),
                ('experience_points', models.PositiveIntegerField(default=0)),
                ('badges', models.JSONField(default=list, help_text='List of earned badge IDs')),
            ],
            options={
                'ordering': ['-total_points'],
            },
        ),
        migrations.AlterModelOptions(
            name='category',
            options={'ordering': ['name'], 'verbose_name_plural': 'categories'},
        ),
        migrations.AlterModelOptions(
            name='quiz',
            options={'ordering': ['-created_at']},
        ),
        migrations.AlterModelOptions(
            name='userquizattempt',
            options={'ordering': ['-started_at']},
        ),
        migrations.AlterUniqueTogether(
            name='userquizattempt',
            unique_together=set(),
        ),
        migrations.AddField(
            model_name='category',
            name='color',
            field=models.CharField(default='primary', max_length=20),
        ),
        migrations.AddField(
            model_name='category',
            name='icon',
            field=models.CharField(default='bi-book', max_length=50),
        ),
        migrations.AddField(
            model_name='category',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='question',
            name='correct_answer',
            field=models.TextField(blank=True, help_text='For short answer questions'),
        ),
        migrations.AddField(
            model_name='question',
            name='difficulty',
            field=models.CharField(choices=[('EASY', 'Easy'), ('MEDIUM', 'Medium'), ('HARD', 'Hard')], default='MEDIUM', max_length=20),
        ),
        migrations.AddField(
            model_name='question',
            name='points',
            field=models.PositiveIntegerField(default=10, help_text='Points for correct answer'),
        ),
        migrations.AddField(
            model_name='question',
            name='question_type',
            field=models.CharField(choices=[('MULTIPLE_CHOICE', 'Multiple Choice'), ('TRUE_FALSE', 'True/False'), ('SHORT_ANSWER', 'Short Answer')], default='MULTIPLE_CHOICE', max_length=20),
        ),
        migrations.AddField(
            model_name='quiz',
            name='average_score',
            field=models.FloatField(default=0.0),
        ),
        migrations.AddField(
            model_name='quiz',
            name='description',
            field=models.TextField(blank=True, help_text='Brief description of the quiz'),
        ),
        migrations.AddField(
            model_name='quiz',
            name='featured_until',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='quiz',
            name='max_attempts',
            field=models.PositiveIntegerField(default=3, help_text='Maximum attempts per user'),
        ),
        migrations.AddField(
            model_name='quiz',
            name='points_reward',
            field=models.PositiveIntegerField(default=100, help_text='Points awarded for completion'),
        ),
        migrations.AddField(
            model_name='quiz',
            name='quiz_type',
            field=models.CharField(choices=[('REGULAR', 'Regular Quiz'), ('DAILY', 'Daily Challenge'), ('FEATURED', 'Featured Quiz'), ('AI_GENERATED', 'AI Generated')], default='REGULAR', max_length=20),
        ),
        migrations.AddField(
            model_name='quiz',
            name='tags',
            field=models.CharField(blank=True, help_text='Comma-separated tags', max_length=200),
        ),
        migrations.AddField(
            model_name='quiz',
            name='time_limit',
            field=models.PositiveIntegerField(default=30, help_text='Time limit in minutes'),
        ),
        migrations.AddField(
            model_name='quiz',
            name='total_attempts',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='quiz',
            name='total_completions',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='userquizattempt',
            name='max_possible_score',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='userquizattempt',
            name='percentage',
            field=models.FloatField(default=0.0),
        ),
        migrations.AddField(
            model_name='userquizattempt',
            name='points_earned',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='userquizattempt',
            name='started_at',
            field=models.DateTimeField(auto_now_add=True, default=datetime.datetime(2025, 7, 6, 17, 56, 55, 953963, tzinfo=datetime.timezone.utc)),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='userquizattempt',
            name='status',
            field=models.CharField(choices=[('IN_PROGRESS', 'In Progress'), ('COMPLETED', 'Completed'), ('ABANDONED', 'Abandoned'), ('TIME_UP', 'Time Up')], default='IN_PROGRESS', max_length=20),
        ),
        migrations.AddField(
            model_name='userquizattempt',
            name='time_taken',
            field=models.DurationField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='question',
            name='correct_option',
            field=models.CharField(blank=True, choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')], max_length=1),
        ),
        migrations.AlterField(
            model_name='question',
            name='option_a',
            field=models.CharField(blank=True, max_length=300),
        ),
        migrations.AlterField(
            model_name='question',
            name='option_b',
            field=models.CharField(blank=True, max_length=300),
        ),
        migrations.AlterField(
            model_name='question',
            name='option_c',
            field=models.CharField(blank=True, max_length=300),
        ),
        migrations.AlterField(
            model_name='question',
            name='option_d',
            field=models.CharField(blank=True, max_length=300),
        ),
        migrations.AlterField(
            model_name='question',
            name='text',
            field=models.TextField(validators=[django.core.validators.MinLengthValidator(10)]),
        ),
        migrations.AlterField(
            model_name='quiz',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='userquizattempt',
            name='completed_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='userquizattempt',
            name='score',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddIndex(
            model_name='quiz',
            index=models.Index(fields=['quiz_type', 'is_published'], name='quizzes_qui_quiz_ty_8a1520_idx'),
        ),
        migrations.AddIndex(
            model_name='quiz',
            index=models.Index(fields=['featured_until'], name='quizzes_qui_feature_7bf01a_idx'),
        ),
        migrations.AddIndex(
            model_name='userquizattempt',
            index=models.Index(fields=['user', 'quiz'], name='quizzes_use_user_id_51af4c_idx'),
        ),
        migrations.AddIndex(
            model_name='userquizattempt',
            index=models.Index(fields=['status', 'completed_at'], name='quizzes_use_status_0618e4_idx'),
        ),
        migrations.AddField(
            model_name='dailychallenge',
            name='quiz',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='daily_challenges', to='quizzes.quiz'),
        ),
        migrations.AlterUniqueTogether(
            name='leaderboard',
            unique_together={('period', 'start_date', 'end_date')},
        ),
        migrations.AddField(
            model_name='userprofile',
            name='user',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='quiz_profile', to=settings.AUTH_USER_MODEL),
        ),
    ]
