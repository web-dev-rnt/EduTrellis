from django.contrib import admin
from .models import ELibraryCourse, ELibraryPDF, ELibraryEnrollment, ELibraryDownload


# Inline PDF display under course
class ELibraryPDFInline(admin.TabularInline):
    model = ELibraryPDF
    extra = 1
    fields = ('title', 'chapter_number', 'order', 'is_preview', 'is_active')
    readonly_fields = ('file_size', 'download_count', 'uploaded_at')
    ordering = ('chapter_number', 'order')


@admin.register(ELibraryCourse)
class ELibraryCourseAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'category', 'instructor', 'difficulty_level',
        'price', 'discount_price', 'is_featured', 'is_active', 
        'is_bestseller', 'total_pdfs', 'enrollment_count', 'created_at'
    )
    list_filter = (
        'category', 'difficulty_level', 'is_featured', 
        'is_active', 'is_bestseller', 'language'
    )
    search_fields = ('title', 'instructor', 'category__name', 'tags')
    readonly_fields = ('total_pdfs', 'total_pages', 'enrollment_count', 'created_at', 'updated_at')
    inlines = [ELibraryPDFInline]
    list_editable = ('is_featured', 'is_active', 'is_bestseller')
    ordering = ('-created_at',)
    save_on_top = True


@admin.register(ELibraryPDF)
class ELibraryPDFAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'course', 'chapter_number', 'order', 'is_preview',
        'is_active', 'page_count', 'file_size', 'download_count', 'uploaded_at'
    )
    list_filter = ('course', 'is_preview', 'is_active')
    search_fields = ('title', 'course__title')
    readonly_fields = ('file_size', 'download_count', 'uploaded_at', 'updated_at')
    ordering = ('course', 'chapter_number', 'order')


@admin.register(ELibraryEnrollment)
class ELibraryEnrollmentAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'payment_status', 'amount_paid', 'enrolled_at')
    list_filter = ('payment_status', 'enrolled_at')
    search_fields = ('user__username', 'course__title', 'payment_id')
    readonly_fields = ('enrolled_at',)
    ordering = ('-enrolled_at',)


@admin.register(ELibraryDownload)
class ELibraryDownloadAdmin(admin.ModelAdmin):
    list_display = ('user', 'pdf', 'downloaded_at', 'ip_address')
    list_filter = ('downloaded_at',)
    search_fields = ('user__username', 'pdf__title', 'ip_address')
    readonly_fields = ('downloaded_at',)
    ordering = ('-downloaded_at',)
