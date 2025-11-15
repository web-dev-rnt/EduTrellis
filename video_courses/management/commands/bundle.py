# product_bundles/management/commands/seed_product_bundles.py

from django.core.management.base import BaseCommand
from django.utils.text import slugify
from django.utils import timezone
from decimal import Decimal
import random

from adminpanel.models import ProductBundle
from video_courses.models import VideoCourse, Category
from live_class.models import LiveClassCourse
from testseries.models import TestSeries
from elibrary.models import ELibraryCourse
from base.models import User


class Command(BaseCommand):
    help = "Seed demo Product Bundles data"

    def handle(self, *args, **kwargs):
        try:
            admin_user = User.objects.filter(is_superuser=True).first()
            if not admin_user:
                self.stdout.write(self.style.ERROR("❌ No admin user found. Create one first."))
                return

            # Create categories if not exist
            cat_names = ["Full Stack Development", "Banking Exams", "Engineering Entrance", "Medical Prep"]
            categories = []
            for name in cat_names:
                cat, _ = Category.objects.get_or_create(name=name, defaults={"slug": slugify(name)})
                categories.append(cat)

            # Fetch existing products
            videos = list(VideoCourse.objects.all()[:5])
            lives = list(LiveClassCourse.objects.all()[:5])
            tests = list(TestSeries.objects.all()[:5])
            elibs = list(ELibraryCourse.objects.all()[:5])

            if not any([videos, lives, tests, elibs]):
                self.stdout.write(self.style.WARNING("⚠️ No products found. Please seed products first."))
                return

            # Delete old demo bundles
            ProductBundle.objects.filter(title__icontains="Demo Bundle").delete()

            # Create demo bundles
            for i in range(1, 6):
                category = random.choice(categories)
                bundle_type = random.choice([
                    'mixed', 'video_only', 'live_only', 'test_only', 'elibrary_only'
                ])

                title = f"Demo Bundle {i} - {category.name}"
                bundle = ProductBundle.objects.create(
                    title=title,
                    slug=slugify(title),
                    description=f"This is a demo bundle {i} including top-rated courses and materials.",
                    short_description="Perfect for students preparing for competitive exams.",
                    bundle_type=bundle_type,
                    category=category,
                    original_price=Decimal("9999.00"),
                    bundle_price=Decimal(random.randint(2999, 6999)),
                    currency="INR",
                    features="Access all included courses\n1 Year Validity\nCertificate on Completion",
                    validity_days=365,
                    start_date=timezone.now().date(),
                    end_date=None,
                    status="active",
                    is_featured=random.choice([True, False]),
                    is_bestseller=random.choice([True, False]),
                    is_trending=random.choice([True, False]),
                    display_order=i,
                    created_by=admin_user
                )

                # Add related products based on bundle type
                if bundle_type in ['mixed', 'video_only']:
                    bundle.video_courses.add(*random.sample(videos, min(2, len(videos))))
                if bundle_type in ['mixed', 'live_only']:
                    bundle.live_classes.add(*random.sample(lives, min(2, len(lives))))
                if bundle_type in ['mixed', 'test_only']:
                    bundle.test_series.add(*random.sample(tests, min(2, len(tests))))
                if bundle_type in ['mixed', 'elibrary_only']:
                    bundle.elibrary_courses.add(*random.sample(elibs, min(2, len(elibs))))

                # Auto-calculate original price
                bundle.original_price = bundle.calculate_original_price()
                bundle.save()

                self.stdout.write(self.style.SUCCESS(f"✅ Created: {bundle.title}"))

            self.stdout.write(self.style.SUCCESS("🎉 Demo Product Bundles created successfully!"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error: {str(e)}"))
