from django.contrib import admin
from .models import LiveClassCourse, LiveClassSession


class LiveClassSessionInline(admin.TabularInline):
    model = LiveClassSession
    extra = 1
    fields = [
        'class_name', 
        'subject', 
        'scheduled_datetime', 
        'duration_minutes', 
        'max_participants', 
        'is_free', 
        'enable_auto_recording'
    ]
    readonly_fields = ['created_at']
    show_change_link = True
    ordering = ['scheduled_datetime']


@admin.register(LiveClassCourse)
class LiveClassCourseAdmin(admin.ModelAdmin):
    list_display = [
        'name', 
        'category_name', 
        'language', 
        'current_price', 
        'original_price', 
        'start_date', 
        'end_date', 
        'is_active', 
        'session_count'
    ]
    
    list_filter = [
        'category',
        'language', 
        'is_active', 
        'start_date',
        'end_date',
        'created_at'
    ]
    
    search_fields = [
        'name', 
        'language', 
        'category__name'
    ]
    
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Course Information', {
            'fields': ('name', 'category', 'language', 'about')
        }),
        ('Pricing', {
            'fields': ('original_price', 'current_price')
        }),
        ('Schedule', {
            'fields': ('start_date', 'end_date')
        }),
        ('Media', {
            'fields': ('banner_image_desktop', 'banner_image_mobile'),
            'classes': ('collapse',)
        }),
        ('Status & Timestamps', {
            'fields': ('is_active', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [LiveClassSessionInline]
    
    date_hierarchy = 'start_date'
    
    list_per_page = 25
    
    actions = ['activate_courses', 'deactivate_courses']
    
    def category_name(self, obj):
        """Display category name"""
        return obj.category_name
    category_name.short_description = 'Category'
    category_name.admin_order_field = 'category__name'
    
    def session_count(self, obj):
        """Display number of sessions in this course"""
        return obj.sessions.count()
    session_count.short_description = 'Sessions'
    
    def activate_courses(self, request, queryset):
        """Bulk activate selected courses"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} course(s) were successfully activated.')
    activate_courses.short_description = "Activate selected courses"
    
    def deactivate_courses(self, request, queryset):
        """Bulk deactivate selected courses"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} course(s) were successfully deactivated.')
    deactivate_courses.short_description = "Deactivate selected courses"


@admin.register(LiveClassSession)
class LiveClassSessionAdmin(admin.ModelAdmin):
    list_display = [
        'class_name', 
        'course', 
        'subject',
        'scheduled_datetime', 
        'duration_minutes', 
        'max_participants', 
        'is_free', 
        'enable_auto_recording',
        'status'
    ]
    
    list_filter = [
        'course',
        'scheduled_datetime', 
        'is_free', 
        'enable_auto_recording',
        'duration_minutes',
        'course__category'
    ]
    
    search_fields = [
        'class_name', 
        'subject',
        'course__name',
        'course__category__name'
    ]
    
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Session Details', {
            'fields': ('course', 'class_name', 'subject')
        }),
        ('Schedule & Duration', {
            'fields': ('scheduled_datetime', 'duration_minutes')
        }),
        ('Participants & Access', {
            'fields': ('max_participants', 'is_free')
        }),
        ('Recording Settings', {
            'fields': ('enable_auto_recording',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    date_hierarchy = 'scheduled_datetime'
    
    list_per_page = 50
    
    ordering = ['scheduled_datetime']
    
    actions = ['enable_recording', 'disable_recording', 'make_free', 'make_paid']
    
    def status(self, obj):
        """Display session status based on datetime"""
        from django.utils import timezone
        now = timezone.now()
        
        if obj.scheduled_datetime > now:
            return "Upcoming"
        elif obj.scheduled_datetime <= now < (obj.scheduled_datetime + timezone.timedelta(minutes=obj.duration_minutes)):
            return "Live"
        else:
            return "Completed"
    status.short_description = 'Status'
    
    def enable_recording(self, request, queryset):
        """Bulk enable recording for selected sessions"""
        updated = queryset.update(enable_auto_recording=True)
        self.message_user(request, f'Recording enabled for {updated} session(s).')
    enable_recording.short_description = "Enable auto recording"
    
    def disable_recording(self, request, queryset):
        """Bulk disable recording for selected sessions"""
        updated = queryset.update(enable_auto_recording=False)
        self.message_user(request, f'Recording disabled for {updated} session(s).')
    disable_recording.short_description = "Disable auto recording"
    
    def make_free(self, request, queryset):
        """Make selected sessions free"""
        updated = queryset.update(is_free=True)
        self.message_user(request, f'{updated} session(s) made free.')
    make_free.short_description = "Make sessions free"
    
    def make_paid(self, request, queryset):
        """Make selected sessions paid"""
        updated = queryset.update(is_free=False)
        self.message_user(request, f'{updated} session(s) made paid.')
    make_paid.short_description = "Make sessions paid"
    
    def get_queryset(self, request):
        """Optimize queries by selecting related objects"""
        return super().get_queryset(request).select_related('course', 'course__category')
