from django.core.management.base import BaseCommand
from faker import Faker
from decimal import Decimal
import random
from django.utils.text import slugify
from django.utils import timezone
from video_courses.models import Category
from testseries.models import TestSeries, Subject, Test, Question

fake = Faker()

class Command(BaseCommand):
    help = "Seed demo TestSeries data with thumbnails, tests, and questions"

    def add_arguments(self, parser):
        parser.add_argument('--series', type=int, default=3, help="Number of test series to create")
        parser.add_argument('--tests', type=int, default=5, help="Number of tests per series")
        parser.add_argument('--questions', type=int, default=10, help="Number of questions per test")

    def handle(self, *args, **options):
        num_series = options['series']
        num_tests = options['tests']
        num_questions = options['questions']

        self.stdout.write(self.style.NOTICE("Seeding demo test series data..."))

        # --- Step 1: Ensure at least one category exists
        categories = list(Category.objects.all())
        if not categories:
            self.stdout.write("⚠️ No categories found, creating some...")
            for i in range(3):
                categories.append(Category.objects.create(
                    name=fake.word().capitalize() + " Category",
                    description=fake.text(100)
                ))

        # --- Step 2: Ensure subjects exist
        subjects = list(Subject.objects.all())
        if not subjects:
            self.stdout.write("⚠️ No subjects found, creating sample subjects...")
            subject_names = ["Physics", "Chemistry", "Mathematics", "Biology", "English"]
            for name in subject_names:
                subjects.append(Subject.objects.create(
                    name=name,
                    code=name[:3].upper(),
                    color=random.choice(["#3B82F6", "#10B981", "#F59E0B", "#EF4444", "#8B5CF6"]),
                ))

        # --- Step 3: Create Test Series
        for _ in range(num_series):
            category = random.choice(categories)
            title = f"{fake.word().capitalize()} Master Test Series"
            test_series = TestSeries.objects.create(
                title=title,
                category=category,
                description=fake.text(200),
                thumbnail="test_series/sample_thumbnail.jpg",  # static file path (place in MEDIA_ROOT/test_series/)
                is_free=random.choice([True, False]),
                price=Decimal(random.randint(0, 999)),
                difficulty=random.choice(["easy", "medium", "hard", "expert"]),
                estimated_duration=f"{random.randint(1,3)}-{random.randint(4,6)} hours per test",
                has_negative_marking=True,
                pass_percentage=random.randint(40, 80),
                is_featured=random.choice([True, False]),
            )

            # --- Step 4: Create Tests inside each series
            for t in range(num_tests):
                test = Test.objects.create(
                    test_series=test_series,
                    title=f"Test {t+1}: {fake.sentence(nb_words=4)}",
                    description=fake.text(150),
                    duration_minutes=random.randint(30, 120),
                    start_time=timezone.now(),
                    end_time=timezone.now() + timezone.timedelta(days=random.randint(10, 30)),
                )

                # --- Step 5: Create Questions per Test
                for q in range(num_questions):
                    question_type = random.choice(["mcq_single", "true_false", "fill_blank"])
                    subject = random.choice(subjects)
                    options = {}
                    correct_answer = {}

                    if question_type == "mcq_single":
                        opts = [fake.word().capitalize() for _ in range(4)]
                        correct = random.choice(opts)
                        options = {str(i+1): o for i, o in enumerate(opts)}
                        correct_answer = {"correct": correct}
                    elif question_type == "true_false":
                        options = {"1": "True", "2": "False"}
                        correct_answer = {"correct": random.choice(["True", "False"])}
                    elif question_type == "fill_blank":
                        options = {}
                        correct_answer = {"correct": fake.word()}

                    Question.objects.create(
                        test=test,
                        subject=subject,
                        question_type=question_type,
                        difficulty=random.choice(["easy", "medium", "hard"]),
                        question_text=fake.sentence(nb_words=12),
                        marks=random.choice([1, 2, 4]),
                        negative_marks=Decimal("0.25"),
                        options=options,
                        correct_answer=correct_answer,
                        explanation=fake.text(100),
                        total_attempts=random.randint(10, 100),
                        correct_attempts=random.randint(5, 90),
                        order=q + 1
                    )

            self.stdout.write(self.style.SUCCESS(f"✅ Created Test Series: {test_series.title} with {num_tests} tests"))

        self.stdout.write(self.style.SUCCESS("🎯 Demo TestSeries data created successfully!"))
