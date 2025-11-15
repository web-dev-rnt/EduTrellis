from django.core.management.base import BaseCommand
from faker import Faker
from datetime import timedelta
import random

from live_class.models import LiveClassCourse, LiveClassSession
from video_courses.models import Category


class Command(BaseCommand):
    help = "Seed sample data for LiveClassCourse and LiveClassSession models"

    def handle(self, *args, **kwargs):
        fake = Faker()
        Faker.seed(0)
        random.seed(0)

        # 1️⃣ Clear old data (optional)
        LiveClassSession.objects.all().delete()
        LiveClassCourse.objects.all().delete()

        self.stdout.write(self.style.WARNING("🧹 Old Live Class data deleted."))

        # 2️⃣ Get existing categories
        categories = list(Category.objects.all())
        if not categories:
            self.stdout.write(self.style.ERROR("⚠️ No categories found in 'Category' table. Please create some first."))
            return

        # 3️⃣ Create LiveClassCourse entries
        num_courses = 5
        courses = []

        for _ in range(num_courses):
            category = random.choice(categories)
            name = fake.catch_phrase()

            course = LiveClassCourse.objects.create(
                name=name,
                language=random.choice(["English", "Hindi", "Bilingual"]),
                original_price=random.randint(1500, 5000),
                current_price=random.randint(500, 2000),
                start_date=fake.date_between(start_date="-10d", end_date="+10d"),
                end_date=fake.date_between(start_date="+11d", end_date="+40d"),
                about=fake.paragraph(nb_sentences=5),
                category=category,
                is_active=True,
            )
            courses.append(course)

        self.stdout.write(self.style.SUCCESS(f"✅ Created {len(courses)} LiveClassCourse records."))

        # 4️⃣ Create sessions for each course
        total_sessions = 0
        for course in courses:
            num_sessions = random.randint(3, 8)
            for _ in range(num_sessions):
                start_time = fake.date_time_between(start_date="-3d", end_date="+15d")
                LiveClassSession.objects.create(
                    course=course,
                    class_name=fake.bs().title(),
                    subject=random.choice(["Math", "Science", "English", "Economics", "Computer Science", "GK"]),
                    scheduled_datetime=start_time,
                    duration_minutes=random.choice([45, 60, 75, 90]),
                    max_participants=random.choice([100, 200, 300]),
                    is_free=random.choice([True, False]),
                    enable_auto_recording=random.choice([True, False]),
                )
                total_sessions += 1

        self.stdout.write(self.style.SUCCESS(f"✅ Created {total_sessions} LiveClassSession records."))
        self.stdout.write(self.style.SUCCESS("🎉 Live class data seeded successfully!"))
