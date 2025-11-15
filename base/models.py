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