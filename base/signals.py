# base/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from live_class.models import LiveClassCourse, LiveClassSession
from .models import User, Notification
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=LiveClassCourse)
def create_free_live_class_notification(sender, instance, created, **kwargs):
    """
    Create notifications for all users when a free live class course is created
    """
    if created and instance.is_free:
        try:
            # Get all active users
            users = User.objects.filter(is_active=True)
            
            # Create notification for each user
            notifications = []
            for user in users:
                notification = Notification(
                    user=user,
                    notification_type='free_live_class',
                    title=f"🎉 Free Live Course: {instance.name}",
                    message=f"Great news! A new free live course '{instance.name}' is now available. Join from {instance.start_date.strftime('%B %d, %Y')} and start learning!",
                    link=f"/live-class/{instance.id}/",
                    related_object_id=instance.id,
                    related_object_type='live_course'
                )
                notifications.append(notification)
            
            # Bulk create notifications
            Notification.objects.bulk_create(notifications)
            logger.info(f"Created {len(notifications)} notifications for free live course: {instance.name}")
            
        except Exception as e:
            logger.error(f"Error creating notifications for free live course: {e}")

@receiver(post_save, sender=LiveClassSession)
def create_free_session_notification(sender, instance, created, **kwargs):
    """
    Create notifications for all users when a free session is created
    """
    if created and instance.is_free:
        try:
            # Get all active users
            users = User.objects.filter(is_active=True)
            
            # Format the session datetime
            session_date = instance.scheduled_datetime.strftime('%B %d, %Y')
            session_time = instance.scheduled_datetime.strftime('%I:%M %p')
            
            # Create notification for each user
            notifications = []
            for user in users:
                notification = Notification(
                    user=user,
                    notification_type='free_live_class',
                    title=f"🆓 Free Session: {instance.class_name}",
                    message=f"Join our free live session '{instance.class_name}' from course '{instance.course.name}' on {session_date} at {session_time}. Duration: {instance.duration_minutes} minutes.",
                    link=f"/live-class/{instance.course.id}/",
                    related_object_id=instance.id,
                    related_object_type='live_session'
                )
                notifications.append(notification)
            
            # Bulk create notifications
            Notification.objects.bulk_create(notifications)
            logger.info(f"Created {len(notifications)} notifications for free session: {instance.class_name}")
            
        except Exception as e:
            logger.error(f"Error creating notifications for free session: {e}")

# Signal for when a paid course becomes free (in case of updates)
@receiver(post_save, sender=LiveClassCourse)
def notify_course_became_free(sender, instance, created, **kwargs):
    """
    Create notifications when an existing course becomes free
    """
    if not created:  # Only for updates, not new courses
        # Check if the course just became free
        if instance.is_free:
            # Check if notifications already exist for this course
            existing_notifications = Notification.objects.filter(
                related_object_id=instance.id,
                related_object_type='live_course',
                notification_type='free_live_class'
            ).exists()
            
            if not existing_notifications:
                try:
                    users = User.objects.filter(is_active=True)
                    notifications = []
                    
                    for user in users:
                        notification = Notification(
                            user=user,
                            notification_type='offer',
                            title=f"🎁 Course Now Free: {instance.name}",
                            message=f"Amazing offer! The course '{instance.name}' is now available for FREE. Don't miss this opportunity!",
                            link=f"/live-class/{instance.id}/",
                            related_object_id=instance.id,
                            related_object_type='live_course'
                        )
                        notifications.append(notification)
                    
                    Notification.objects.bulk_create(notifications)
                    logger.info(f"Created {len(notifications)} notifications for course that became free: {instance.name}")
                    
                except Exception as e:
                    logger.error(f"Error creating notifications for course that became free: {e}")

# Signal for when a paid session becomes free
@receiver(post_save, sender=LiveClassSession)
def notify_session_became_free(sender, instance, created, **kwargs):
    """
    Create notifications when an existing session becomes free
    """
    if not created and instance.is_free:
        # Check if notifications already exist for this session
        existing_notifications = Notification.objects.filter(
            related_object_id=instance.id,
            related_object_type='live_session',
            notification_type='free_live_class'
        ).exists()
        
        if not existing_notifications:
            try:
                users = User.objects.filter(is_active=True)
                
                session_date = instance.scheduled_datetime.strftime('%B %d, %Y')
                session_time = instance.scheduled_datetime.strftime('%I:%M %p')
                
                notifications = []
                for user in users:
                    notification = Notification(
                        user=user,
                        notification_type='offer',
                        title=f"🎁 Free Session Alert: {instance.class_name}",
                        message=f"Special offer! The session '{instance.class_name}' is now FREE to attend. Join us on {session_date} at {session_time}.",
                        link=f"/live-class/{instance.course.id}/",
                        related_object_id=instance.id,
                        related_object_type='live_session'
                    )
                    notifications.append(notification)
                
                Notification.objects.bulk_create(notifications)
                logger.info(f"Created {len(notifications)} notifications for session that became free: {instance.class_name}")
                
            except Exception as e:
                logger.error(f"Error creating notifications for session that became free: {e}")