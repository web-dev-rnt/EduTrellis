from django.core.management.base import BaseCommand
from faker import Faker
from decimal import Decimal
import random
from video_courses.models import Category, VideoCourse, WhatYouLearnPoint, CourseInclude, CourseVideo

fake = Faker()

class Command(BaseCommand):
    help = "Seed database with sample data for testing"

    def add_arguments(self, parser):
        parser.add_argument('--categories', type=int, default=3, help="Number of categories to create")
        parser.add_argument('--courses', type=int, default=5, help="Number of courses to create per category")
        parser.add_argument('--videos', type=int, default=5, help="Number of videos per course")

    def handle(self, *args, **options):
        num_categories = options['categories']
        num_courses = options['courses']
        num_videos = options['videos']

        self.stdout.write(self.style.NOTICE("Seeding test data..."))

        # Create categories
        categories = []
        for _ in range(num_categories):
            cat = Category.objects.create(
                name=fake.unique.word().capitalize() + " Category",
                description=fake.text(100),
            )
            categories.append(cat)
        self.stdout.write(self.style.SUCCESS(f"✅ Created {len(categories)} categories"))

        # Create courses for each category
        for category in categories:
            for _ in range(num_courses):
                course = VideoCourse.objects.create(
                    name=fake.unique.sentence(nb_words=3),
                    category=category,
                    description=fake.text(200),
                    original_price=Decimal(random.randint(1000, 5000)),
                    selling_price=Decimal(random.randint(500, 3000)),
                    currency="INR",
                    instructor_name=fake.name(),
                    instructor_headline=fake.sentence(nb_words=6),
                    is_premium=random.choice([True, False]),
                    is_bestseller=random.choice([True, False]),
                    rating=round(random.uniform(3.5, 5.0), 2),
                    rating_count=random.randint(10, 1000),
                    total_hours=Decimal(round(random.uniform(1, 20), 2)),
                )

                # Create WhatYouLearn points
                for _ in range(random.randint(3, 6)):
                    WhatYouLearnPoint.objects.create(
                        course=course,
                        text=fake.sentence(nb_words=8)
                    )

                # Create CourseIncludes
                for _ in range(random.randint(2, 5)):
                    CourseInclude.objects.create(
                        course=course,
                        label=fake.sentence(nb_words=5)
                    )

                # Create CourseVideos
                for i in range(num_videos):
                    CourseVideo.objects.create(
                        course=course,
                        title=f"Lesson {i+1}: {fake.sentence(nb_words=4)}",
                        duration_seconds=random.randint(60, 600),
                        is_preview=random.choice([True, False]),
                        file="video_courses/sample_video.mp4",  # Placeholder path
                    )

        self.stdout.write(self.style.SUCCESS("🎉 Test data created successfully!"))
