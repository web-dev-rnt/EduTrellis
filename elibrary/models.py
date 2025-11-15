from django.db import models
from base.models import User
from django.core.validators import FileExtensionValidator
from video_courses.models import Category  # Import from existing category model
import os
import math

class ELibraryCourse(models.Model):
    DIFFICULTY_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    short_description = models.CharField(max_length=300, help_text="Brief description for card view")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='elibrary_courses')
    instructor = models.CharField(max_length=100)
    difficulty_level = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='beginner')
    
    # Pricing
    is_free = models.BooleanField(default=False, help_text="Make this course free for all users")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    
    # Media
    cover_image = models.ImageField(upload_to='elibrary/courses/covers/', blank=True, null=True)
    preview_pdf = models.FileField(
        upload_to='elibrary/courses/previews/', 
        blank=True, null=True,
        validators=[FileExtensionValidator(allowed_extensions=['pdf'])]
    )
    
    # Status and Features
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_bestseller = models.BooleanField(default=False)
    
    # Stats
    total_pdfs = models.PositiveIntegerField(default=0)
    total_pages = models.PositiveIntegerField(default=0, help_text="Approximate total pages")
    enrollment_count = models.PositiveIntegerField(default=0)
    
    # Metadata
    tags = models.CharField(max_length=500, blank=True, help_text="Comma-separated tags")
    language = models.CharField(max_length=50, default='English')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    @property
    def current_price(self):
        """Return 0 if course is free, otherwise return discount_price or price"""
        if self.is_free:
            return 0
        return self.discount_price if self.discount_price else self.price

    @property
    def has_discount(self):
        """Check if course has discount (only applicable for paid courses)"""
        if self.is_free:
            return False
        return self.discount_price is not None and self.discount_price < self.price

    @property
    def discount_percentage(self):
        """Calculate discount percentage (only for paid courses)"""
        if self.is_free or not self.has_discount:
            return 0
        return round(((self.price - self.discount_price) / self.price) * 100)

    def save(self, *args, **kwargs):
        # Update total PDFs count
        if self.pk:
            self.total_pdfs = self.pdfs.filter(is_active=True).count()
        super().save(*args, **kwargs)

class ELibraryPDF(models.Model):
    course = models.ForeignKey(ELibraryCourse, on_delete=models.CASCADE, related_name='pdfs')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    file = models.FileField(
        upload_to='elibrary/pdfs/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf'])]
    )
    
    # Organization
    chapter_number = models.PositiveIntegerField(default=1, help_text="Chapter or section number")
    order = models.PositiveIntegerField(default=0, help_text="Order within chapter")
    
    # Metadata
    page_count = models.PositiveIntegerField(default=0)
    file_size = models.CharField(max_length=20, blank=True)
    is_preview = models.BooleanField(default=False, help_text="Available as free preview")
    is_active = models.BooleanField(default=True)
    
    # Stats
    download_count = models.PositiveIntegerField(default=0)
    
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['chapter_number', 'order', 'title']

    def __str__(self):
        return f"{self.course.title} - {self.title}"

    def save(self, *args, **kwargs):
        if self.file:
            # Calculate file size
            self.file_size = self.format_file_size(self.file.size)
        super().save(*args, **kwargs)

    def format_file_size(self, size_bytes):
        if size_bytes == 0:
            return "0B"
        size_name = ["B", "KB", "MB", "GB", "TB"]
        i = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, i)
        s = round(size_bytes / p, 2)
        return f"{s} {size_name[i]}"

class ELibraryEnrollment(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(ELibraryCourse, on_delete=models.CASCADE)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payment_id = models.CharField(max_length=100, blank=True, null=True)
    enrolled_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'course']

    # def __str__(self):
    #     return f"{self.user.username} - {self.course.title}"

class ELibraryDownload(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    pdf = models.ForeignKey(ELibraryPDF, on_delete=models.CASCADE)
    downloaded_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)

    # def __str__(self):
    #     return f"{self.user.first_name} - {self.pdf.title}"
