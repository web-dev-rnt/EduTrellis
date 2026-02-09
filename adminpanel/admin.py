from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.utils import timezone
from .models import (
    Notification, DeveloperPopup,
    Coupon, CouponUsage, UserCoupon, Banner, StatCard, CTASection,
    AboutUsSection, WhyChooseUsItem, ServiceItem, NavbarSettings,
    FooterSettings, FooterLink, FooterLegalLink, SMTPConfiguration,
    ProductBundle
)


# ============================================
# NOTIFICATION ADMIN
# ============================================
@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['title', 'scheduled_time', 'is_active', 'is_scheduled_status', 'created_at']
    list_filter = ['is_active', 'scheduled_time', 'created_at']
    search_fields = ['title', 'body']
    list_editable = ['is_active']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-scheduled_time', '-created_at']
    
    fieldsets = (
        ('Notification Content', {
            'fields': ('title', 'body', 'link')
        }),
        ('Schedule Settings', {
            'fields': ('scheduled_time', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def is_scheduled_status(self, obj):
        if obj.is_scheduled:
            return format_html('<span style="color: orange;">⏰ Scheduled</span>')
        return format_html('<span style="color: green;">✓ Active Now</span>')
    is_scheduled_status.short_description = 'Schedule Status'


# ============================================
# DEVELOPER POPUP ADMIN
# ============================================
@admin.register(DeveloperPopup)
class DeveloperPopupAdmin(admin.ModelAdmin):
    list_display = ['developer_name', 'email', 'is_active', 'delay_seconds', 'updated_at']
    list_filter = ['is_active', 'show_once_per_session', 'created_at']
    search_fields = ['developer_name', 'email', 'tagline']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Profile Information', {
            'fields': ('profile_image', 'greeting_text', 'developer_name', 'tagline')
        }),
        ('Message Section', {
            'fields': ('message_title', 'message_body')
        }),
        ('Contact Information', {
            'fields': ('email', 'whatsapp_number', 'linkedin_url', 'linkedin_display_text')
        }),
        ('Footer', {
            'fields': ('footer_message',)
        }),
        ('Display Settings', {
            'fields': ('is_active', 'delay_seconds', 'show_once_per_session')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def image_preview(self, obj):
        if obj.profile_image:
            return format_html('<img src="{}" width="50" height="50" style="border-radius: 50%; object-fit: cover;" />', obj.profile_image.url)
        return "No Image"
    image_preview.short_description = 'Profile'


# ============================================
# COUPON ADMIN
# ============================================
@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ['code', 'discount_display', 'status', 'usage_display', 'validity_period', 'is_valid_now']
    list_filter = ['status', 'discount_type', 'created_at', 'valid_from', 'valid_to']
    search_fields = ['code', 'description']
    readonly_fields = ['used_count', 'created_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('code', 'description', 'created_by', 'status')
        }),
        ('Discount Settings', {
            'fields': ('discount_type', 'discount_value', 'minimum_amount', 'maximum_discount')
        }),
        ('Usage Settings', {
            'fields': ('usage_limit', 'used_count')
        }),
        ('Validity Period', {
            'fields': ('valid_from', 'valid_to')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    actions = ['activate_coupons', 'deactivate_coupons']
    
    def discount_display(self, obj):
        return obj.get_discount_display()
    discount_display.short_description = 'Discount'
    
    def usage_display(self, obj):
        percentage = (obj.used_count / obj.usage_limit) * 100 if obj.usage_limit > 0 else 0
        color = 'red' if percentage >= 90 else 'orange' if percentage >= 70 else 'green'
        return format_html(
            '<span style="color: {};">{}/{}</span>',
            color, obj.used_count, obj.usage_limit
        )
    usage_display.short_description = 'Usage'
    
    def validity_period(self, obj):
        return f"{obj.valid_from.strftime('%Y-%m-%d')} to {obj.valid_to.strftime('%Y-%m-%d')}"
    validity_period.short_description = 'Valid Period'
    
    def is_valid_now(self, obj):
        is_valid = obj.is_valid()
        return format_html(
            '<span style="color: {};">{}</span>',
            'green' if is_valid else 'red',
            '✓ Valid' if is_valid else '✗ Invalid'
        )
    is_valid_now.short_description = 'Status'
    
    def activate_coupons(self, request, queryset):
        queryset.update(status='active')
        self.message_user(request, f'{queryset.count()} coupons activated.')
    activate_coupons.short_description = 'Activate selected coupons'
    
    def deactivate_coupons(self, request, queryset):
        queryset.update(status='inactive')
        self.message_user(request, f'{queryset.count()} coupons deactivated.')
    deactivate_coupons.short_description = 'Deactivate selected coupons'


@admin.register(CouponUsage)
class CouponUsageAdmin(admin.ModelAdmin):
    list_display = ['coupon_code', 'user_email', 'discount_amount', 'order_id', 'used_at', 'ip_address']
    list_filter = ['used_at', 'coupon__discount_type']
    search_fields = ['coupon__code', 'user__email', 'order_id', 'ip_address']
    readonly_fields = ['used_at']
    date_hierarchy = 'used_at'
    
    def coupon_code(self, obj):
        return obj.coupon.code
    coupon_code.short_description = 'Coupon Code'
    
    def user_email(self, obj):
        return obj.user.email if obj.user else 'Anonymous'
    user_email.short_description = 'User'


@admin.register(UserCoupon)
class UserCouponAdmin(admin.ModelAdmin):
    list_display = ['user_email', 'coupon_code', 'assigned_at', 'is_used', 'used_at']
    list_filter = ['is_used', 'assigned_at', 'used_at']
    search_fields = ['user__email', 'coupon__code']
    readonly_fields = ['assigned_at', 'used_at']
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User Email'
    
    def coupon_code(self, obj):
        return obj.coupon.code
    coupon_code.short_description = 'Coupon Code'


# ============================================
# BANNER ADMIN
# ============================================
@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ['title', 'image_preview', 'is_active', 'order', 'has_link', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['title', 'alt_text']
    list_editable = ['is_active', 'order']
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="30" style="object-fit: cover;" />', obj.image.url)
        return "No Image"
    image_preview.short_description = 'Preview'
    
    def has_link(self, obj):
        return '✓' if obj.link_url else '✗'
    has_link.short_description = 'Has Link'


# ============================================
# STAT CARD ADMIN
# ============================================
@admin.register(StatCard)
class StatCardAdmin(admin.ModelAdmin):
    list_display = ['label', 'number', 'icon_type', 'icon_preview', 'is_active', 'order']
    list_editable = ['is_active', 'order']
    list_filter = ['is_active', 'icon_type']
    search_fields = ['label', 'number']
    
    fieldsets = (
        ('Content', {
            'fields': ('number', 'label')
        }),
        ('Icon Settings', {
            'fields': ('icon_type', 'icon', 'icon_color', 'icon_image')
        }),
        ('Display Settings', {
            'fields': ('is_active', 'order')
        })
    )
    
    def icon_preview(self, obj):
        return format_html(obj.get_icon_display())
    icon_preview.short_description = 'Icon Preview'


# ============================================
# CTA SECTION ADMIN
# ============================================
@admin.register(CTASection)
class CTASectionAdmin(admin.ModelAdmin):
    list_display = ['title', 'button_text', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['title', 'button_text']


# ============================================
# ABOUT US SECTION ADMIN
# ============================================
@admin.register(AboutUsSection)
class AboutUsSectionAdmin(admin.ModelAdmin):
    list_display = ['company_name', 'heading', 'is_active', 'updated_at']
    list_filter = ['is_active']
    search_fields = ['company_name', 'heading', 'description']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('company_name', 'heading', 'description', 'logo', 'is_active')
        }),
        ('Contact Information', {
            'fields': ('address', 'email', 'phone', 'phone_hours')
        }),
        ('Social Media', {
            'fields': ('facebook_url', 'twitter_url', 'linkedin_url', 'instagram_url', 'telegram_url')
        }),
        ('Map', {
            'fields': ('map_embed_url',)
        })
    )


@admin.register(WhyChooseUsItem)
class WhyChooseUsItemAdmin(admin.ModelAdmin):
    list_display = ['title', 'icon_class', 'is_active', 'order']
    list_editable = ['is_active', 'order']
    list_filter = ['is_active']
    search_fields = ['title', 'description']


@admin.register(ServiceItem)
class ServiceItemAdmin(admin.ModelAdmin):
    list_display = ['service_name', 'icon_class', 'is_active', 'order']
    list_editable = ['is_active', 'order']
    list_filter = ['is_active']
    search_fields = ['service_name', 'service_description']


# ============================================
# NAVBAR SETTINGS ADMIN
# ============================================
@admin.register(NavbarSettings)
class NavbarSettingsAdmin(admin.ModelAdmin):
    list_display = ['contact_number', 'contact_type', 'contact_hours', 'is_active', 'updated_at']
    list_filter = ['is_active', 'contact_type']
    
    fieldsets = (
        ('Logo & Favicon', {
            'fields': ('logo', 'favicon')
        }),
        ('Contact Settings', {
            'fields': ('contact_number', 'contact_hours', 'contact_type')
        }),
        ('Search Settings', {
            'fields': ('search_placeholder',)
        }),
        ('Status', {
            'fields': ('is_active',)
        })
    )
    
    def has_add_permission(self, request):
        # Only allow one instance
        return not NavbarSettings.objects.exists()


# ============================================
# FOOTER SETTINGS ADMIN
# ============================================
@admin.register(FooterSettings)
class FooterSettingsAdmin(admin.ModelAdmin):
    list_display = ['email', 'is_active', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('logo', 'email', 'copyright_text', 'is_active')
        }),
        ('App Store Links', {
            'fields': ('google_play_url', 'app_store_url')
        }),
        ('Social Media', {
            'fields': ('facebook_url', 'twitter_url', 'youtube_url', 'linkedin_url', 'instagram_url', 'telegram_url')
        })
    )
    
    def has_add_permission(self, request):
        # Only allow one instance
        return not FooterSettings.objects.exists()


@admin.register(FooterLink)
class FooterLinkAdmin(admin.ModelAdmin):
    list_display = ['section', 'title', 'url', 'order', 'is_active']
    list_filter = ['section', 'is_active']
    list_editable = ['order', 'is_active']
    search_fields = ['title', 'url']


@admin.register(FooterLegalLink)
class FooterLegalLinkAdmin(admin.ModelAdmin):
    list_display = ['title', 'url', 'order', 'is_active']
    list_editable = ['order', 'is_active']
    search_fields = ['title', 'url']


# ============================================
# SMTP CONFIGURATION ADMIN
# ============================================
@admin.register(SMTPConfiguration)
class SMTPConfigurationAdmin(admin.ModelAdmin):
    list_display = ['name', 'email_host_user', 'email_host', 'email_port', 'is_active', 'test_status', 'last_tested']
    list_filter = ['is_active', 'test_status', 'email_use_tls', 'email_use_ssl']
    search_fields = ['name', 'email_host_user', 'email_host']
    readonly_fields = ['last_tested', 'test_status', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Configuration', {
            'fields': ('name', 'email_backend', 'is_active')
        }),
        ('SMTP Settings', {
            'fields': ('email_host', 'email_port', 'email_use_tls', 'email_use_ssl')
        }),
        ('Authentication', {
            'fields': ('email_host_user', 'email_host_password', 'default_from_email')
        }),
        ('Test Results', {
            'fields': ('test_status', 'last_tested'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    actions = ['test_smtp_connection']
    
    def test_smtp_connection(self, request, queryset):
        for smtp_config in queryset:
            success, message = smtp_config.test_connection()
            if success:
                messages.success(request, f'{smtp_config.name}: {message}')
            else:
                messages.error(request, f'{smtp_config.name}: {message}')
    test_smtp_connection.short_description = 'Test SMTP connection'


# ============================================
# PRODUCT BUNDLE ADMIN
# ============================================
@admin.register(ProductBundle)
class ProductBundleAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'bundle_type', 'category', 'price_display', 
        'discount_badge', 'total_products_count', 'status', 
        'is_featured', 'is_available_status', 'created_at'
    ]
    list_filter = [
        'status', 'bundle_type', 'category', 'is_free', 
        'is_featured', 'is_bestseller', 'is_trending', 'created_at'
    ]
    search_fields = ['title', 'slug', 'description', 'short_description']
    list_editable = ['status', 'is_featured']
    readonly_fields = [
        'slug', 'current_enrollments', 'total_views', 'total_purchases',
        'rating', 'rating_count', 'created_at', 'updated_at'
    ]
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ['video_courses', 'live_classes', 'test_series', 'elibrary_courses']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'description', 'short_description', 'bundle_type', 'category')
        }),
        ('Media', {
            'fields': ('thumbnail', 'banner_image')
        }),
        ('Pricing', {
            'fields': ('is_free', 'original_price', 'bundle_price', 'currency'),
            'description': 'Set is_free to True for free bundles. Prices will be auto-set to 0.'
        }),
        ('Products in Bundle', {
            'fields': ('video_courses', 'live_classes', 'test_series', 'elibrary_courses'),
            'classes': ('collapse',)
        }),
        ('Features & Benefits', {
            'fields': ('features',),
            'description': 'Enter one feature per line'
        }),
        ('Validity & Availability', {
            'fields': ('validity_days', 'start_date', 'end_date')
        }),
        ('Status & Visibility', {
            'fields': ('status', 'is_featured', 'is_bestseller', 'is_trending', 'display_order')
        }),
        ('Enrollment Limits', {
            'fields': ('max_enrollments', 'current_enrollments')
        }),
        ('Analytics (Read Only)', {
            'fields': ('total_views', 'total_purchases', 'rating', 'rating_count'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def price_display(self, obj):
        if obj.is_free:
            return format_html('<span style="color: green; font-weight: bold;">FREE</span>')
        return format_html(
            '<del style="color: #999;">₹{}</del> <strong style="color: green;">₹{}</strong>',
            obj.original_price, obj.bundle_price
        )
    price_display.short_description = 'Price'
    
    def discount_badge(self, obj):
        discount = obj.discount_percentage
        if discount > 0:
            color = 'green' if discount >= 50 else 'orange' if discount >= 25 else 'blue'
            return format_html(
                '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 4px;">{:.0f}% OFF</span>',
                color, discount
            )
        return '-'
    discount_badge.short_description = 'Discount'
    
    def total_products_count(self, obj):
        count = obj.total_products
        return format_html('<strong>{}</strong> products', count)
    total_products_count.short_description = 'Products'
    
    def is_available_status(self, obj):
        if obj.is_available:
            return format_html('<span style="color: green;">✓ Available</span>')
        return format_html('<span style="color: red;">✗ Unavailable</span>')
    is_available_status.short_description = 'Availability'
    
    actions = ['make_active', 'make_inactive', 'mark_as_featured', 'calculate_prices']
    
    def make_active(self, request, queryset):
        queryset.update(status='active')
        self.message_user(request, f'{queryset.count()} bundles activated.')
    make_active.short_description = 'Mark selected bundles as Active'
    
    def make_inactive(self, request, queryset):
        queryset.update(status='inactive')
        self.message_user(request, f'{queryset.count()} bundles deactivated.')
    make_inactive.short_description = 'Mark selected bundles as Inactive'
    
    def mark_as_featured(self, request, queryset):
        queryset.update(is_featured=True)
        self.message_user(request, f'{queryset.count()} bundles marked as featured.')
    mark_as_featured.short_description = 'Mark selected bundles as Featured'
    
    def calculate_prices(self, request, queryset):
        for bundle in queryset:
            bundle.original_price = bundle.calculate_original_price()
            bundle.save(update_fields=['original_price'])
        self.message_user(request, f'Original prices calculated for {queryset.count()} bundles.')
    calculate_prices.short_description = 'Auto-calculate original prices'


# ============================================
# ADMIN SITE CUSTOMIZATION
# ============================================
admin.site.site_header = "EduGorilla Admin Panel"
admin.site.site_title = "EduGorilla Admin"
admin.site.index_title = "Welcome to EduGorilla Administration"