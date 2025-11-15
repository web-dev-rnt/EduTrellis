from django.core.management.base import BaseCommand
from faker import Faker
import random
from decimal import Decimal

from elibrary.models import ELibraryCourse, ELibraryPDF, ELibraryEnrollment, ELibraryDownload
from video_courses.models import Category
from base.models import User


class Command(BaseCommand):
    help = "Seed new random data for ELibrary models (adds without deleting old data)"

    def handle(self, *args, **kwargs):
        fake = Faker()
        Faker.seed()
        random.seed()

        # 1️⃣ Fetch existing users and categories
        users = list(User.objects.all())
        categories = list(Category.objects.all())

        if not users:
            self.stdout.write(self.style.ERROR("⚠️ No users found. Please create some users first."))
            return

        if not categories:
            self.stdout.write(self.style.ERROR("⚠️ No categories found. Please create at least one category first."))
            return

        # 2️⃣ Create New eLibrary Courses
        num_new_courses = random.randint(3, 8)
        new_courses = []
        difficulty_levels = ['beginner', 'intermediate', 'advanced']

        for _ in range(num_new_courses):
            category = random.choice(categories)
            instructor = fake.name()
            title = f"{fake.catch_phrase()} ({fake.word().capitalize()} Edition)"

            price = Decimal(random.randint(500, 3000))
            has_discount = random.choice([True, False])
            discount_price = price - Decimal(random.randint(100, 700)) if has_discount else None

            course = ELibraryCourse.objects.create(
                title=title,
                description=fake.paragraph(nb_sentences=10),
                short_description=fake.sentence(nb_words=10),
                category=category,
                instructor=instructor,
                difficulty_level=random.choice(difficulty_levels),
                price=price,
                discount_price=discount_price,
                is_featured=random.choice([True, False]),
                is_active=True,
                is_bestseller=random.choice([True, False]),
                total_pdfs=0,
                total_pages=random.randint(40, 300),
                enrollment_count=0,
                tags=", ".join(fake.words(nb=6)),
                language=random.choice(["English", "Hindi", "Bilingual"]),
                created_by=random.choice(users),
            )
            new_courses.append(course)

        self.stdout.write(self.style.SUCCESS(f"✅ Added {len(new_courses)} new ELibraryCourse records."))

        # 3️⃣ Create PDFs for the new courses
        all_pdfs = []
        for course in new_courses:
            num_pdfs = random.randint(4, 10)
            total_pages = 0

            for i in range(1, num_pdfs + 1):
                pages = random.randint(6, 25)
                total_pages += pages

                pdf = ELibraryPDF.objects.create(
                    course=course,
                    title=f"Module {i}: {fake.catch_phrase()}",
                    description=fake.paragraph(nb_sentences=5),
                    chapter_number=i,
                    order=i,
                    page_count=pages,
                    file_size=f"{random.randint(300, 8000)} KB",
                    is_preview=(i == 1),
                    is_active=True,
                    download_count=random.randint(0, 150),
                    uploaded_by=random.choice(users),
                )
                all_pdfs.append(pdf)

            course.total_pdfs = num_pdfs
            course.total_pages = total_pages
            course.save()

        self.stdout.write(self.style.SUCCESS(f"✅ Added {len(all_pdfs)} new ELibraryPDF records."))

        # 4️⃣ Create random Enrollments
        total_enrollments = 0
        for course in new_courses:
            enrolled_users = random.sample(users, min(len(users), random.randint(2, 6)))

            for user in enrolled_users:
                if not ELibraryEnrollment.objects.filter(user=user, course=course).exists():
                    ELibraryEnrollment.objects.create(
                        user=user,
                        course=course,
                        payment_status=random.choice(['completed', 'pending']),
                        amount_paid=course.current_price,
                        payment_id=fake.uuid4(),
                    )
                    total_enrollments += 1

            course.enrollment_count += len(enrolled_users)
            course.save()

        self.stdout.write(self.style.SUCCESS(f"✅ Added {total_enrollments} new ELibraryEnrollment records."))

        # 5️⃣ Randomly simulate some Downloads
        total_downloads = 0
        for pdf in random.sample(all_pdfs, min(25, len(all_pdfs))):
            user = random.choice(users)
            ELibraryDownload.objects.create(
                user=user,
                pdf=pdf,
                ip_address=fake.ipv4()
            )
            total_downloads += 1

        self.stdout.write(self.style.SUCCESS(f"✅ Added {total_downloads} new ELibraryDownload records."))
        self.stdout.write(self.style.SUCCESS("🎉 New eLibrary data seeded successfully without deleting existing records!"))
