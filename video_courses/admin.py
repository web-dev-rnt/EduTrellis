from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db import models
from .models import Category, VideoCourse, WhatYouLearnPoint, CourseInclude, CourseVideo


class WhatYouLearnInline(admin.TabularInline):
    model = WhatYouLearnPoint
    extra = 1
    fields = ("text",)
    show_change_link = True
    verbose_name = "Learning Point"
    verbose_name_plural = "What You'll Learn"


class CourseIncludeInline(admin.TabularInline):
    model = CourseInclude
    extra = 1
    fields = ("label",)
    show_change_link = True
    verbose_name = "Course Include"
    verbose_name_plural = "What's Included"


class CourseVideoInline(admin.TabularInline):
    model = CourseVideo
    extra = 1
    fields = ("title", "is_preview", "file", "thumb_image", "duration_display")
    readonly_fields = ("duration_display",)
    show_change_link = True
    verbose_name = "Course Video"
    verbose_name_plural = "Course Videos"
    
    def duration_display(self, obj):
        """Display duration in minutes and seconds"""
        if obj.duration_seconds:
            minutes = obj.duration_seconds // 60
            seconds = obj.duration_seconds % 60
            return f"{minutes}m {seconds}s"
        return "Unknown"
    duration_display.short_description = "Duration"


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "course_count", "created_at")
    search_fields = ("name", "description")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("name",)
    readonly_fields = ("created_at", "updated_at")
    
    fieldsets = (
        ("Basic Information", {
            "fields": ("name", "slug", "description")
        }),
        ("Timestamps", {
            "classes": ("collapse",),
            "fields": ("created_at", "updated_at")
        }),
    )
    
    def course_count(self, obj):
        """Display number of courses in this category"""
        count = obj.video_courses.count()
        if count > 0:
            url = reverse("admin:video_courses_videocourse_changelist")
            return format_html(
                '<a href="{}?category__id__exact={}">{} courses</a>',
                url, obj.pk, count
            )
        return "0 courses"
    course_count.short_description = "Courses"
    course_count.admin_order_field = "video_courses__count"
    
    def get_queryset(self, request):
        """Optimize queries by annotating course count"""
        return super().get_queryset(request).annotate(
            course_count=models.Count('video_courses')
        )


@admin.register(VideoCourse)
class VideoCourseAdmin(admin.ModelAdmin):
    list_display = (
        "id", "name", "category_link", "thumbnail_preview",
        "price_display", "stats_display", "video_count",
        "instructor_name", "flags_display", "updated_at"
    )
    list_filter = (
        "category", "is_premium", "is_bestseller", 
        "created_at", "updated_at"
    )
    search_fields = (
        "name", "description", "instructor_name", 
        "instructor_headline", "slug"
    )
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = (
        "created_at", "updated_at", "thumbnail_preview_large",
        "total_duration_display", "video_stats"
    )
    
    fieldsets = (
        ("Course Information", {
            "fields": ("name", "slug", "category", "description")
        }),
        ("Media", {
            "fields": ("thumbnail", "thumbnail_preview_large")
        }),
        ("Pricing", {
            "fields": (("original_price", "selling_price", "currency"),)
        }),
        ("Course Statistics", {
            "fields": (
                ("rating", "rating_count"), 
                ("total_hours", "total_duration_display"),
                "video_stats"
            )
        }),
        ("Flags & Features", {
            "fields": (("is_premium", "is_bestseller"),)
        }),
        ("Instructor Information", {
            "fields": ("instructor_name", "instructor_headline", "instructor_avatar")
        }),
        ("Timestamps", {
            "classes": ("collapse",),
            "fields": ("created_at", "updated_at")
        }),
    )
    
    inlines = [WhatYouLearnInline, CourseIncludeInline, CourseVideoInline]
    ordering = ("-updated_at",)
    list_per_page = 25
    
    actions = ["make_premium", "remove_premium", "mark_bestseller", "unmark_bestseller"]
    
    def thumbnail_preview(self, obj):
        """Small thumbnail preview for list view"""
        if obj.thumbnail:
            return format_html(
                '<img src="{}" style="width: 50px; height: 30px; object-fit: cover; border-radius: 4px;" />',
                obj.thumbnail.url
            )
        return "No image"
    thumbnail_preview.short_description = "Thumbnail"
    
    def thumbnail_preview_large(self, obj):
        """Large thumbnail preview for detail view"""
        if obj.thumbnail:
            return format_html(
                '<img src="{}" style="width: 200px; height: auto; border-radius: 8px;" />',
                obj.thumbnail.url
            )
        return "No thumbnail uploaded"
    thumbnail_preview_large.short_description = "Current Thumbnail"
    
    def category_link(self, obj):
        """Clickable category link"""
        if obj.category:
            url = reverse("admin:video_courses_category_change", args=[obj.category.pk])
            return format_html('<a href="{}">{}</a>', url, obj.category.name)
        return "No Category"
    category_link.short_description = "Category"
    category_link.admin_order_field = "category__name"
    
    def price_display(self, obj):
        """Display pricing information"""
        if obj.selling_price != obj.original_price:
            return format_html(
                '<strong>₹{}</strong><br/><small style="text-decoration: line-through; color: #666;">₹{}</small>',
                obj.selling_price, obj.original_price
            )
        return f"₹{obj.selling_price}"
    price_display.short_description = "Price"
    price_display.admin_order_field = "selling_price"
    
    def stats_display(self, obj):
        """Display rating and reviews"""
        if obj.rating > 0:
            stars = "⭐" * int(obj.rating)
            return format_html(
                '{} {}<br/><small>{} reviews</small>',
                stars[:5], obj.rating, obj.rating_count
            )
        return "No ratings"
    stats_display.short_description = "Rating"
    stats_display.admin_order_field = "rating"
    
    def flags_display(self, obj):
        """Display premium and bestseller flags"""
        flags = []
        if obj.is_premium:
            flags.append('<span style="background: #f59e0b; color: white; padding: 2px 6px; border-radius: 4px; font-size: 10px;">PREMIUM</span>')
        if obj.is_bestseller:
            flags.append('<span style="background: #10b981; color: white; padding: 2px 6px; border-radius: 4px; font-size: 10px;">BESTSELLER</span>')
        return format_html(' '.join(flags)) if flags else "-"
    flags_display.short_description = "Flags"
    
    def video_count(self, obj):
        """Display number of videos"""
        count = obj.videos.count()
        if count > 0:
            url = reverse("admin:video_courses_coursevideo_changelist")
            return format_html(
                '<a href="{}?course__id__exact={}">{} videos</a>',
                url, obj.pk, count
            )
        return "0 videos"
    video_count.short_description = "Videos"
    
    def total_duration_display(self, obj):
        """Calculate and display total duration from all videos"""
        total_seconds = sum(video.duration_seconds for video in obj.videos.all())
        if total_seconds:
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            return f"{hours}h {minutes}m"
        return "0h 0m"
    total_duration_display.short_description = "Actual Duration"
    
    def video_stats(self, obj):
        """Display video statistics"""
        videos = obj.videos.all()
        total_videos = videos.count()
        preview_videos = videos.filter(is_preview=True).count()
        
        if total_videos > 0:
            return format_html(
                '<strong>{}</strong> total videos<br/>'
                '<strong>{}</strong> preview videos<br/>'
                '<strong>{}</strong> paid videos',
                total_videos, preview_videos, total_videos - preview_videos
            )
        return "No videos uploaded"
    video_stats.short_description = "Video Statistics"
    
    # Bulk actions
    def make_premium(self, request, queryset):
        """Mark selected courses as premium"""
        updated = queryset.update(is_premium=True)
        self.message_user(request, f'{updated} course(s) marked as premium.')
    make_premium.short_description = "Mark as premium"
    
    def remove_premium(self, request, queryset):
        """Remove premium status from selected courses"""
        updated = queryset.update(is_premium=False)
        self.message_user(request, f'{updated} course(s) removed from premium.')
    remove_premium.short_description = "Remove premium status"
    
    def mark_bestseller(self, request, queryset):
        """Mark selected courses as bestseller"""
        updated = queryset.update(is_bestseller=True)
        self.message_user(request, f'{updated} course(s) marked as bestseller.')
    mark_bestseller.short_description = "Mark as bestseller"
    
    def unmark_bestseller(self, request, queryset):
        """Remove bestseller status from selected courses"""
        updated = queryset.update(is_bestseller=False)
        self.message_user(request, f'{updated} course(s) removed from bestseller.')
    unmark_bestseller.short_description = "Remove bestseller status"
    
    def get_queryset(self, request):
        """Optimize queries"""
        return super().get_queryset(request).select_related(
            'category'
        ).prefetch_related('videos')


@admin.register(CourseVideo)
class CourseVideoAdmin(admin.ModelAdmin):
    list_display = (
        "title", "course_link", "duration_display", 
        "is_preview", "file_size_display", "thumbnail_preview", 
        "created_at"
    )
    list_filter = ("course", "is_preview", "created_at")
    search_fields = ("title", "course__name")
    ordering = ("course", "id")
    readonly_fields = ("duration_display", "file_info", "created_at", "updated_at")
    
    fieldsets = (
        ("Video Information", {
            "fields": ("course", "title", "is_preview")
        }),
        ("Media Files", {
            "fields": ("file", "thumb_image", "file_info")
        }),
        ("Technical Details", {
            "fields": ("duration_display",)
        }),
        ("Timestamps", {
            "classes": ("collapse",),
            "fields": ("created_at", "updated_at")
        }),
    )
    
    def course_link(self, obj):
        """Clickable course link"""
        url = reverse("admin:video_courses_videocourse_change", args=[obj.course.pk])
        return format_html('<a href="{}">{}</a>', url, obj.course.name)
    course_link.short_description = "Course"
    course_link.admin_order_field = "course__name"
    
    def duration_display(self, obj):
        """Display duration in readable format"""
        if obj.duration_seconds:
            minutes = obj.duration_seconds // 60
            seconds = obj.duration_seconds % 60
            return f"{minutes}m {seconds}s ({obj.duration_seconds}s)"
        return "Unknown duration"
    duration_display.short_description = "Duration"
    
    def file_size_display(self, obj):
        """Display file size in readable format"""
        if obj.file:
            try:
                size = obj.file.size
                if size < 1024:
                    return f"{size} B"
                elif size < 1024 * 1024:
                    return f"{size / 1024:.1f} KB"
                elif size < 1024 * 1024 * 1024:
                    return f"{size / (1024 * 1024):.1f} MB"
                else:
                    return f"{size / (1024 * 1024 * 1024):.1f} GB"
            except Exception:
                return "Unknown size"
        return "No file"
    file_size_display.short_description = "File Size"
    
    def file_info(self, obj):
        """Display detailed file information"""
        if obj.file:
            try:
                return format_html(
                    '<strong>File:</strong> {}<br/>'
                    '<strong>Size:</strong> {}<br/>'
                    '<strong>Duration:</strong> {}',
                    obj.file.name.split('/')[-1],
                    self.file_size_display(obj),
                    self.duration_display(obj)
                )
            except Exception:
                return "File information unavailable"
        return "No file uploaded"
    file_info.short_description = "File Information"
    
    def thumbnail_preview(self, obj):
        """Display video thumbnail"""
        if obj.thumb_image:
            return format_html(
                '<img src="{}" style="width: 60px; height: 40px; object-fit: cover; border-radius: 4px;" />',
                obj.thumb_image.url
            )
        return "No thumbnail"
    thumbnail_preview.short_description = "Thumbnail"


@admin.register(WhatYouLearnPoint)
class WhatYouLearnPointAdmin(admin.ModelAdmin):
    list_display = ("course_link", "text_preview", "created_at")
    list_filter = ("course", "created_at")
    search_fields = ("text", "course__name")
    ordering = ("course", "id")
    readonly_fields = ("created_at", "updated_at")
    
    def course_link(self, obj):
        """Clickable course link"""
        url = reverse("admin:video_courses_videocourse_change", args=[obj.course.pk])
        return format_html('<a href="{}">{}</a>', url, obj.course.name)
    course_link.short_description = "Course"
    course_link.admin_order_field = "course__name"
    
    def text_preview(self, obj):
        """Display truncated text"""
        return obj.text[:80] + "..." if len(obj.text) > 80 else obj.text
    text_preview.short_description = "Learning Point"


@admin.register(CourseInclude)
class CourseIncludeAdmin(admin.ModelAdmin):
    list_display = ("course_link", "label_preview", "created_at")
    list_filter = ("course", "created_at")
    search_fields = ("label", "course__name")
    ordering = ("course", "id")
    readonly_fields = ("created_at", "updated_at")
    
    def course_link(self, obj):
        """Clickable course link"""
        url = reverse("admin:video_courses_videocourse_change", args=[obj.course.pk])
        return format_html('<a href="{}">{}</a>', url, obj.course.name)
    course_link.short_description = "Course"
    course_link.admin_order_field = "course__name"
    
    def label_preview(self, obj):
        """Display truncated label"""
        return obj.label[:60] + "..." if len(obj.label) > 60 else obj.label
    label_preview.short_description = "Include Item"
