# base/models.py
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils import timezone
from datetime import timedelta
import random
import string

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email must be provided')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        return self.create_user(email, password, **extra_fields)

        
class User(AbstractBaseUser, PermissionsMixin):
    # Basic Information
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150, blank=True)
    middle_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    age = models.PositiveIntegerField(null=True, blank=True)
    contact_number = models.CharField(max_length=20, blank=True)
    
    # Gender Choices
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
        ('N', 'Prefer not to say'),
    ]
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True)
    
    # Profile Image
    profile_image = models.ImageField(upload_to='profile_pics/', null=True, blank=True)
    
    # Account Status
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    objects = UserManager()

    def __str__(self):
        return self.email

    def get_full_name(self):
        parts = [self.first_name, self.middle_name, self.last_name]
        full_name = ' '.join(filter(None, [p.strip() for p in parts]))
        return full_name

    def get_short_name(self):
        return self.first_name or ''

    def get_full_name_or_email(self) -> str:
        full = self.get_full_name()
        return full or self.email


class OTPVerification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='otp_verifications')
    otp_code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    verification_type = models.CharField(
        max_length=20,
        choices=[('email', 'Email Verification'), ('password_reset', 'Password Reset')],
        default='email'
    )

    def save(self, *args, **kwargs):
        if not self.otp_code:
            self.otp_code = self.generate_otp()
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=10)
        super().save(*args, **kwargs)

    def generate_otp(self):
        return ''.join(random.choices(string.digits, k=6))

    def is_valid(self):
        return not self.is_used and timezone.now() <= self.expires_at

    def __str__(self):
        return f"OTP for {self.user.email} - {self.otp_code}"

    class Meta:
        ordering = ['-created_at']


class Payment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    razorpay_order_id = models.CharField(max_length=100, unique=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_signature = models.CharField(max_length=255, blank=True, null=True)
    
    # Course related fields
    course_type = models.CharField(max_length=50, choices=[
        ('video_course', 'Video Course'),
        ('live_class', 'Live Class'),
        ('test_series', 'Test Series'),
        ('elibrary', 'E-Library'),
        ('bundle', 'Product Bundle')
    ])
    course_id = models.IntegerField()
    course_name = models.CharField(max_length=255)
    
    amount = models.IntegerField()  # Amount in paise
    currency = models.CharField(max_length=10, default='INR')
    status = models.CharField(max_length=50, default='Created', choices=[
        ('Created', 'Created'),
        ('Success', 'Success'),
        ('Failed', 'Failed')
    ])
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.razorpay_order_id} - {self.course_name} - {self.status}"

    class Meta:
        ordering = ['-created_at']


class UserCourseAccess(models.Model):
    """Track user access to purchased courses"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='course_access')
    course_id = models.IntegerField()
    course_type = models.CharField(max_length=50)  # 'video_course', 'live_class', etc.
    payment = models.ForeignKey('Payment', on_delete=models.SET_NULL, null=True, blank=True)
    access_granted_at = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    expires_at = models.DateTimeField(null=True, blank=True)  # For time-limited access
    
    class Meta:
        unique_together = ('user', 'course_id', 'course_type')
        ordering = ['-access_granted_at']
        verbose_name = 'User Course Access'
        verbose_name_plural = 'User Course Access Records'
    
    def __str__(self):
        return f"{self.user.first_name} - {self.course_type}:{self.course_id}"
    
    @property
    def is_expired(self):
        """Check if access has expired"""
        if not self.expires_at:
            return False
        return timezone.now() > self.expires_at
    
    @property
    def has_access(self):
        """Check if user currently has access"""
        return self.is_active and not self.is_expired
    

#Notification model to your existing base/models.py

class Notification(models.Model):
    """Enhanced Notification model with tracking"""
    NOTIFICATION_TYPES = [
        ('free_live_class', 'Free Live Class'),
        ('free_session', 'Free Session'),
        ('course_update', 'Course Update'),
        ('announcement', 'Announcement'),
        ('offer', 'Special Offer'),
        ('reminder', 'Reminder'),
        ('system', 'System Notice'),
        ('custom', 'Custom Message'),
    ]
    
    PRIORITY_LEVELS = [
        (0, 'Normal'),
        (1, 'High'),
        (2, 'Urgent'),
    ]
    
    # Core fields
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications', null=True, blank=True)
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=255)
    message = models.TextField()
    link = models.CharField(max_length=500, blank=True, null=True)
    
    # Status fields
    is_read = models.BooleanField(default=False)
    is_clicked = models.BooleanField(default=False)
    
    # Tracking fields
    sent_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    clicked_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Related object tracking
    related_object_id = models.IntegerField(null=True, blank=True)
    related_object_type = models.CharField(max_length=50, blank=True, null=True)
    
    # Additional metadata
    priority = models.IntegerField(default=0, choices=PRIORITY_LEVELS)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    # Targeting
    is_global = models.BooleanField(default=False, help_text="Send to all users")
    target_group = models.CharField(max_length=100, blank=True, help_text="Target user group")
    
    # Admin tracking
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_notifications')
    
    class Meta:
        ordering = ['-priority', '-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['created_at']),
            models.Index(fields=['related_object_type', 'related_object_id']),
            models.Index(fields=['is_global']),
        ]
    
    def __str__(self):
        if self.user:
            return f"{self.user.email} - {self.title}"
        return f"Global - {self.title}"
    
    def mark_as_read(self):
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()
    
    def mark_as_clicked(self):
        if not self.is_clicked:
            self.is_clicked = True
            self.clicked_at = timezone.now()
            self.save()
    
    @property
    def is_expired(self):
        """Check if notification has expired"""
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False
    
    @property
    def engagement_rate(self):
        """Calculate engagement rate for analytics"""
        if self.is_clicked:
            return 100
        elif self.is_read:
            return 50
        return 0

class NotificationBatch(models.Model):
    """Track batch notifications sent"""
    title = models.CharField(max_length=255)
    notification_type = models.CharField(max_length=50)
    total_sent = models.IntegerField(default=0)
    total_read = models.IntegerField(default=0)
    total_clicked = models.IntegerField(default=0)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    @property
    def read_rate(self):
        if self.total_sent > 0:
            return (self.total_read / self.total_sent) * 100
        return 0
    
    @property
    def click_rate(self):
        if self.total_sent > 0:
            return (self.total_clicked / self.total_sent) * 100
        return 0
    
    class Meta:
        ordering = ['-created_at']