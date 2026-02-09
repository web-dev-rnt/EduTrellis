# base/management/commands/create_free_notifications.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from live_class.models import LiveClassCourse, LiveClassSession
from base.models import User, Notification
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Create notifications for existing free courses and sessions'
    
    def handle(self, *args, **kwargs):
        """Create notifications for all existing free content"""
        
        # Get all active users
        users = User.objects.filter(is_active=True)
        
        # Process free courses
        free_courses = LiveClassCourse.objects.filter(is_free=True, is_active=True)
        course_notifications = []
        
        for course in free_courses:
            # Check if notification already exists
            existing = Notification.objects.filter(
                related_object_id=course.id,
                related_object_type='live_course'
            ).exists()
            
            if not existing:
                for user in users:
                    notification = Notification(
                        user=user,
                        notification_type='free_live_class',
                        title=f"🎉 Free Live Course: {course.name}",
                        message=f"Check out this free live course: '{course.name}'. Start date: {course.start_date.strftime('%B %d, %Y')}",
                        link=f"/live-class/{course.id}/",
                        related_object_id=course.id,
                        related_object_type='live_course'
                    )
                    course_notifications.append(notification)
        
        # Process free sessions
        free_sessions = LiveClassSession.objects.filter(
            is_free=True,
            scheduled_datetime__gte=timezone.now()  # Only future sessions
        )
        session_notifications = []
        
        for session in free_sessions:
            # Check if notification already exists
            existing = Notification.objects.filter(
                related_object_id=session.id,
                related_object_type='live_session'
            ).exists()
            
            if not existing:
                session_date = session.scheduled_datetime.strftime('%B %d, %Y')
                session_time = session.scheduled_datetime.strftime('%I:%M %p')
                
                for user in users:
                    notification = Notification(
                        user=user,
                        notification_type='free_live_class',
                        title=f"🆓 Free Session: {session.class_name}",
                        message=f"Free session available: '{session.class_name}' on {session_date} at {session_time}",
                        link=f"/live-class/{session.course.id}/",
                        related_object_id=session.id,
                        related_object_type='live_session'
                    )
                    session_notifications.append(notification)
        
        # Bulk create notifications
        if course_notifications:
            Notification.objects.bulk_create(course_notifications)
            self.stdout.write(
                self.style.SUCCESS(
                    f'Created {len(course_notifications)} course notifications'
                )
            )
        
        if session_notifications:
            Notification.objects.bulk_create(session_notifications)
            self.stdout.write(
                self.style.SUCCESS(
                    f'Created {len(session_notifications)} session notifications'
                )
            )
        
        if not course_notifications and not session_notifications:
            self.stdout.write(
                self.style.WARNING('No new notifications to create')
            )