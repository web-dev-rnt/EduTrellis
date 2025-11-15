from django.db import models
from base.models import User
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.text import slugify
from video_courses.models import Category
import uuid
import json

class TestSeries(models.Model):
    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
        ('expert', 'Expert'),
    ]
    
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='test_series')
    description = models.TextField()
    thumbnail = models.ImageField(upload_to='test_series/', blank=True, null=True)
    
    # Pricing
    is_free = models.BooleanField(default=False)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Test Configuration
    total_tests = models.PositiveIntegerField(default=0)
    total_questions = models.PositiveIntegerField(default=0)
    total_marks = models.PositiveIntegerField(default=0)
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default='medium')
    estimated_duration = models.CharField(max_length=50, help_text="e.g., '2-3 hours per test'")
    
    # Features
    has_negative_marking = models.BooleanField(default=True)
    negative_marks = models.DecimalField(max_digits=5, decimal_places=2, default=0.25)
    pass_percentage = models.PositiveIntegerField(default=40, validators=[MinValueValidator(1), MaxValueValidator(100)])
    
    # Visibility
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    
    # Analytics
    total_attempts = models.PositiveIntegerField(default=0)
    average_score = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Test Series"

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
        
    def update_stats(self):
        """Update test series statistics"""
        tests = self.tests.filter(is_active=True)
        self.total_tests = tests.count()
        self.total_questions = sum(test.total_questions for test in tests)
        self.total_marks = sum(test.total_marks for test in tests)
        self.save(update_fields=['total_tests', 'total_questions', 'total_marks'])


class Subject(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)
    color = models.CharField(max_length=7, default='#3B82F6')
    icon = models.CharField(max_length=50, blank=True, help_text="FontAwesome icon class")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Test(models.Model):
    test_series = models.ForeignKey(TestSeries, on_delete=models.CASCADE, related_name='tests')
    title = models.CharField(max_length=200)
    slug = models.SlugField(blank=True)
    description = models.TextField(blank=True)
    
    # Test Configuration
    duration_minutes = models.PositiveIntegerField(help_text="Test duration in minutes")
    total_questions = models.PositiveIntegerField(default=0)
    total_marks = models.PositiveIntegerField(default=0)
    
    # Question Distribution
    easy_questions = models.PositiveIntegerField(default=0)
    medium_questions = models.PositiveIntegerField(default=0)
    hard_questions = models.PositiveIntegerField(default=0)
    
    # Settings
    shuffle_questions = models.BooleanField(default=True)
    show_result_immediately = models.BooleanField(default=True)
    allow_review = models.BooleanField(default=True)
    max_attempts = models.PositiveIntegerField(default=1)
    
    # Scheduling
    start_time = models.DateTimeField(blank=True, null=True)
    end_time = models.DateTimeField(blank=True, null=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['test_series', 'created_at']
        unique_together = ['test_series', 'slug']

    def __str__(self):
        return f"{self.test_series.title} - {self.title}"

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while Test.objects.filter(test_series=self.test_series, slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        
        super().save(*args, **kwargs)
        
    def update_stats(self):
        """Update test statistics"""
        questions = self.questions.all()
        self.total_questions = questions.count()
        self.total_marks = sum(q.marks for q in questions)
        self.easy_questions = questions.filter(difficulty='easy').count()
        self.medium_questions = questions.filter(difficulty='medium').count()
        self.hard_questions = questions.filter(difficulty='hard').count()
        self.save(update_fields=['total_questions', 'total_marks', 'easy_questions', 'medium_questions', 'hard_questions'])

    @property
    def is_available(self):
        now = timezone.now()
        if self.start_time and now < self.start_time:
            return False
        if self.end_time and now > self.end_time:
            return False
        return True


class Question(models.Model):
    QUESTION_TYPES = [
        ('mcq_single', 'Multiple Choice (Single Answer)'),
        ('mcq_multiple', 'Multiple Choice (Multiple Answers)'),
        ('fill_blank', 'Fill in the Blank'),
        ('true_false', 'True/False'),
        ('numerical', 'Numerical Answer'),
    ]
    
    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    ]
    
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='questions')
    subject = models.ForeignKey(Subject, on_delete=models.SET_NULL, null=True, blank=True)
    
    question_type = models.CharField(max_length=15, choices=QUESTION_TYPES, default='mcq_single')
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default='medium')
    
    question_text = models.TextField()
    question_image = models.ImageField(upload_to='questions/', blank=True, null=True)
    
    # Marking scheme
    marks = models.PositiveIntegerField(default=1)
    negative_marks = models.DecimalField(max_digits=5, decimal_places=2, default=0.25)
    
    # Options (stored as JSON)
    # Format: {"a": "Option A", "b": "Option B", "c": "Option C", "d": "Option D"}
    options = models.JSONField(default=dict, help_text="Store options as JSON")
    
    # Correct Answer (stored as JSON)
    # Format for single: {"answer": "a"}
    # Format for multiple: {"answers": ["a", "c"]}
    # Format for text: {"answer": "correct text"}
    correct_answer = models.JSONField(default=dict, help_text="Store correct answer(s)")
    
    explanation = models.TextField(blank=True, help_text="Explanation for the answer")
    solution_image = models.ImageField(upload_to='solutions/', blank=True, null=True)
    solution_video_url = models.URLField(blank=True, null=True, help_text="YouTube or video URL")
    
    # Analytics
    total_attempts = models.PositiveIntegerField(default=0)
    correct_attempts = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'created_at']

    def __str__(self):
        return f"Q{self.order}: {self.question_text[:50]}..."

    @property
    def accuracy_rate(self):
        if self.total_attempts == 0:
            return 0
        return round((self.correct_attempts / self.total_attempts) * 100, 1)


class TestAttempt(models.Model):
    STATUS_CHOICES = [
        ('started', 'Started'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('submitted', 'Submitted'),
        ('expired', 'Expired'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='test_attempts')
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='attempts')
    
    # Attempt Info
    attempt_number = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='started')
    
    # Timing
    started_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(blank=True, null=True)
    time_spent = models.DurationField(blank=True, null=True)
    remaining_time = models.PositiveIntegerField(default=0, help_text="Remaining time in seconds")
    
    # Scoring
    total_questions = models.PositiveIntegerField(default=0)
    attempted_questions = models.PositiveIntegerField(default=0)
    correct_answers = models.PositiveIntegerField(default=0)
    wrong_answers = models.PositiveIntegerField(default=0)
    
    total_marks = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    marks_obtained = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    percentage_score = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    
    # Pass/Fail
    passed = models.BooleanField(default=False)
    
    # Analytics
    subject_wise_score = models.JSONField(default=dict, blank=True)
    difficulty_wise_score = models.JSONField(default=dict, blank=True)
    question_wise_time = models.JSONField(default=dict, blank=True)
    
    # Rank (if applicable)
    rank = models.PositiveIntegerField(blank=True, null=True)
    percentile = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    
    is_reviewed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['user', 'test', 'attempt_number']
        indexes = [
            models.Index(fields=['user', 'test', 'status']),
            models.Index(fields=['test', 'submitted_at']),
        ]

    def __str__(self):
        return f"{self.user.get_username()} - {self.test.title} (Attempt {self.attempt_number})"
    
    @property
    def skipped_questions(self):
        return self.total_questions - self.attempted_questions
    
    @property
    def accuracy_percentage(self):
        if self.attempted_questions == 0:
            return 0
        return round((self.correct_answers / self.attempted_questions) * 100, 2)
    
    def calculate_rank(self):
        """Calculate rank among all attempts for this test"""
        better_attempts = TestAttempt.objects.filter(
            test=self.test,
            status='submitted',
            marks_obtained__gt=self.marks_obtained
        ).count()
        self.rank = better_attempts + 1
        
        # Calculate percentile
        total_attempts = TestAttempt.objects.filter(
            test=self.test,
            status='submitted'
        ).count()
        
        if total_attempts > 0:
            self.percentile = round(((total_attempts - self.rank + 1) / total_attempts) * 100, 2)
        
        self.save(update_fields=['rank', 'percentile'])


class StudentAnswer(models.Model):
    """Stores individual answers for each question in a test attempt"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    attempt = models.ForeignKey(TestAttempt, on_delete=models.CASCADE, related_name='student_answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='student_answers')
    
    # Answer Data
    # Format for single choice: {"answer": "a"}
    # Format for multiple choice: {"answers": ["a", "c"]}
    # Format for text/numerical: {"answer": "user input"}
    selected_answer = models.JSONField(default=dict, blank=True)
    
    # Evaluation
    is_correct = models.BooleanField(default=False)
    marks_obtained = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    
    # Time tracking
    time_spent = models.PositiveIntegerField(default=0, help_text="Time spent in seconds")
    
    # Flags
    is_marked_for_review = models.BooleanField(default=False)
    is_visited = models.BooleanField(default=True)
    is_attempted = models.BooleanField(default=False)
    
    # Timestamps
    first_visited_at = models.DateTimeField(auto_now_add=True)
    answered_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['attempt', 'question']
        ordering = ['question__order']
        indexes = [
            models.Index(fields=['attempt', 'is_correct']),
            models.Index(fields=['question', 'is_correct']),
        ]

    def __str__(self):
        return f"{self.attempt.user.get_username()} - Q{self.question.order} - {'✓' if self.is_correct else '✗'}"
    
    @property
    def answer_display(self):
        """Return formatted answer for display"""
        if not self.selected_answer:
            return "Not Attempted"
        
        if 'answer' in self.selected_answer:
            return str(self.selected_answer['answer']).upper()
        elif 'answers' in self.selected_answer:
            return ', '.join(str(a).upper() for a in self.selected_answer['answers'])
        return "Invalid Answer"
    
    @property
    def correct_answer_display(self):
        """Return formatted correct answer for display"""
        correct = self.question.correct_answer
        
        if 'answer' in correct:
            return str(correct['answer']).upper()
        elif 'answers' in correct:
            return ', '.join(str(a).upper() for a in correct['answers'])
        return "N/A"


class TestAttemptLog(models.Model):
    """Logs all activities during a test attempt for security and analytics"""
    
    ACTION_CHOICES = [
        ('started', 'Test Started'),
        ('question_viewed', 'Question Viewed'),
        ('answer_selected', 'Answer Selected'),
        ('answer_changed', 'Answer Changed'),
        ('marked_review', 'Marked for Review'),
        ('unmarked_review', 'Unmarked Review'),
        ('tab_switch', 'Tab Switched'),
        ('window_blur', 'Window Lost Focus'),
        ('submitted', 'Test Submitted'),
        ('auto_submitted', 'Auto Submitted (Time Up)'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    attempt = models.ForeignKey(TestAttempt, on_delete=models.CASCADE, related_name='activity_logs')
    question = models.ForeignKey(Question, on_delete=models.SET_NULL, null=True, blank=True)
    
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    description = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['attempt', 'action']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.attempt.user.get_username()} - {self.action} - {self.created_at}"


class TestReview(models.Model):
    """Student reviews and ratings for tests"""
    
    attempt = models.OneToOneField(TestAttempt, on_delete=models.CASCADE, related_name='review')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='reviews')
    
    # Rating (1-5 stars)
    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Rating from 1 to 5 stars"
    )
    
    # Review text
    review_text = models.TextField(blank=True)
    
    # Specific ratings
    difficulty_rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        blank=True,
        null=True
    )
    quality_rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        blank=True,
        null=True
    )
    
    # Flags
    is_approved = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['user', 'test']

    def __str__(self):
        return f"{self.user.get_username()} - {self.test.title} - {self.rating}★"