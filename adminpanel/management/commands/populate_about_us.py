# adminpanel/management/commands/populate_about_us.py
from django.core.management.base import BaseCommand
from adminpanel.models import AboutUsSection, WhyChooseUsItem, ServiceItem

class Command(BaseCommand):
    help = 'Populate default About Us data'
    
    def handle(self, *args, **options):
        # Create default About Us section
        about_us, created = AboutUsSection.objects.get_or_create(
            defaults={
                'company_name': 'EduGorilla Community Pvt. Ltd.',
                'heading': 'About EduGorilla',
                'description': '''India's fastest-growing one-stop exam prep platform (Trusted by over 4 crore users!).
We empower exam aspirants with affordable online live classes, mock tests, e-books, and personalized learning journeys across 1,600+ national and state exams. Maximize your success with best-in-class technology, analytics, and top educators!''',
                'address': '6th Floor, Intech Capital, Vibhuti Khand, Gomti Nagar, Lucknow - 226010, India',
                'email': 'info@edugorilla.com',
                'phone': '0522-3514751',
                'phone_hours': '(10 AM to 7 PM)',
                'facebook_url': 'https://facebook.com/edugorilla',
                'twitter_url': 'https://twitter.com/edugorilla',
                'linkedin_url': 'https://linkedin.com/company/edugorilla',
                'instagram_url': 'https://instagram.com/edugorilla',
                'telegram_url': 'https://t.me/edugorilla',
                'map_embed_url': 'https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3559.179356267426!2d81.01998567588361!3d26.868361676681647!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x399be3b383c2f1d7%3A0x45a6a4568b63d9ed!2sIntech%20Capital%2C%20Vibhuti%20Khand%2C%20Gomti%20Nagar%2C%20Lucknow%2C%20Uttar%20Pradesh%20226010!5e0!3m2!1sen!2sin!4v1711914801650!5m2!1sen!2sin',
            }
        )
        
        # Create default Why Choose Us items
        why_choose_items = [
            {
                'icon_class': 'fa fa-user-circle',
                'title': 'Trusted by 4+ crore learners',
                'description': 'Trusted by <b>4+ crore learners</b> and 10,000+ institutions',
                'order': 1
            },
            {
                'icon_class': 'fa fa-magic',
                'title': 'Proven exam results',
                'description': '<b>Proven exam results:</b> Thousands of toppers every year',
                'order': 2
            },
            {
                'icon_class': 'fa fa-thumbs-up',
                'title': 'Shortest path to selection',
                'description': '<b>Shortest path to selection</b> – with analytics & improvements',
                'order': 3
            },
            {
                'icon_class': 'fa fa-star',
                'title': 'Highest-rated platform',
                'description': '<b>Highest-rated platform/app</b> among students',
                'order': 4
            },
            {
                'icon_class': 'fa fa-shield',
                'title': '100% safe & ad-free',
                'description': '<b>100% safe & ad-free</b> learning environment',
                'order': 5
            },
        ]
        
        for item_data in why_choose_items:
            WhyChooseUsItem.objects.get_or_create(
                title=item_data['title'],
                defaults=item_data
            )
        
        # Create default Service items
        service_items = [
            {
                'icon_class': 'fa fa-video-camera',
                'service_name': 'Live & Interactive Classes',
                'service_description': 'Learn from top educators in real-time with two-way doubt resolution and personal mentoring.',
                'order': 1
            },
            {
                'icon_class': 'fa fa-file-text',
                'service_name': 'Extensive Test Series',
                'service_description': 'Mock exams, practice sets, PYQs, and AI-powered analytics for targeted competitive exam prep.',
                'order': 2
            },
            {
                'icon_class': 'fa fa-book',
                'service_name': 'E-Books & E-Library',
                'service_description': 'Downloadable, exam-focused e-books, summaries, and revision notes—anywhere, anytime.',
                'order': 3
            },
            {
                'icon_class': 'fa fa-bar-chart',
                'service_name': 'Personalized Analytics',
                'service_description': 'Smart progress reports, benchmarking, and improvement suggestions unique to every learner.',
                'order': 4
            },
            {
                'icon_class': 'fa fa-mobile',
                'service_name': 'Anytime, Anywhere Access',
                'service_description': 'Mobile apps and web for seamless learning across all your devices.',
                'order': 5
            },
        ]
        
        for item_data in service_items:
            ServiceItem.objects.get_or_create(
                service_name=item_data['service_name'],
                defaults=item_data
            )
        
        self.stdout.write(
            self.style.SUCCESS('Successfully populated About Us data')
        )
