# live_class/models.py
from django.db import models
from django.utils.text import slugify
from video_courses.models import Category


class LiveClassCourse(models.Model):
    name = models.CharField(max_length=220, unique=True)
    language = models.CharField(max_length=64)
    original_price = models.DecimalField(max_digits=10, decimal_places=2)
    current_price = models.DecimalField(max_digits=10, decimal_places=2)
    is_free = models.BooleanField(default=False, help_text="Check if this is a free course")
    banner_image_desktop = models.ImageField(upload_to='live_courses/banner_desktop/', blank=True, null=True)
    banner_image_mobile = models.ImageField(upload_to='live_courses/banner_mobile/', blank=True, null=True)
    start_date = models.DateField()
    end_date = models.DateField()
    about = models.TextField(blank=True)
    category = models.ForeignKey(
        Category, 
        on_delete=models.SET_NULL,
        null=True, 
        blank=True,
        related_name='live_class_courses',
        verbose_name='Category'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    @property
    def category_name(self):
        """Return category name for display purposes"""
        return self.category.name if self.category else "No Category"
    
    @property
    def display_price(self):
        """Return display price or 'Free' text"""
        if self.is_free:
            return "Free"
        return f"₹{self.current_price}"
    
    @property
    def course_type(self):
        """Return course type for filtering"""
        return "Free" if self.is_free else "Paid"


class LiveClassSession(models.Model):
    course = models.ForeignKey(
        LiveClassCourse, 
        on_delete=models.CASCADE, 
        related_name='sessions'
    )
    class_name = models.CharField(max_length=200)
    subject = models.CharField(max_length=200, blank=True, null=True)
    scheduled_datetime = models.DateTimeField()
    duration_minutes = models.PositiveIntegerField(default=60)
    max_participants = models.PositiveIntegerField(default=100)
    is_free = models.BooleanField(default=False, help_text="Override course pricing for this session")
    enable_auto_recording = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['scheduled_datetime']

    def __str__(self):
        return f"{self.course.name} - {self.class_name}"
