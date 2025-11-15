from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.utils import timezone
from .models import (
    Coupon, CouponUsage, UserCoupon, Banner, StatCard, CTASection,
    AboutUsSection, WhyChooseUsItem, ServiceItem, NavbarSettings,
    FooterSettings, FooterLink, FooterLegalLink, SMTPConfiguration
)


# Coupon Admin
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
    actions = ['activate_coupons', 'deactivate_coupons', 'generate_coupon_code']
    
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


# Banner Admin
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


# Stat Card Admin
@admin.register(StatCard)
class StatCardAdmin(admin.ModelAdmin):
    list_display = ['icon', 'number', 'label', 'is_active', 'order']
    list_editable = ['is_active', 'order']
    list_filter = ['is_active']


# CTA Section Admin
@admin.register(CTASection)
class CTASectionAdmin(admin.ModelAdmin):
    list_display = ['title', 'button_text', 'is_active', 'created_at']
    list_filter = ['is_active']


# About Us Section Admin
@admin.register(AboutUsSection)
class AboutUsSectionAdmin(admin.ModelAdmin):
    list_display = ['company_name', 'heading', 'is_active', 'updated_at']
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


@admin.register(ServiceItem)
class ServiceItemAdmin(admin.ModelAdmin):
    list_display = ['service_name', 'icon_class', 'is_active', 'order']
    list_editable = ['is_active', 'order']
    list_filter = ['is_active']


# Navbar Settings Admin
@admin.register(NavbarSettings)
class NavbarSettingsAdmin(admin.ModelAdmin):
    list_display = ['contact_number', 'contact_hours', 'is_active', 'updated_at']
    
    def has_add_permission(self, request):
        # Only allow one instance
        return not NavbarSettings.objects.exists()


# Footer Settings Admin
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


@admin.register(FooterLegalLink)
class FooterLegalLinkAdmin(admin.ModelAdmin):
    list_display = ['title', 'url', 'order', 'is_active']
    list_editable = ['order', 'is_active']


# SMTP Configuration Admin
@admin.register(SMTPConfiguration)
class SMTPConfigurationAdmin(admin.ModelAdmin):
    list_display = ['name', 'email_host_user', 'email_host', 'email_port', 'is_active', 'test_status', 'last_tested']
    list_filter = ['is_active', 'test_status', 'email_use_tls', 'email_use_ssl']
    search_fields = ['name', 'email_host_user', 'email_host']
    readonly_fields = ['last_tested', 'test_status']
    
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
    
    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(self.readonly_fields)
        if obj:  # Editing existing object
            readonly_fields.extend(['created_at', 'updated_at'])
        return readonly_fields


# Customize Admin Site
admin.site.site_header = "EduGorilla Admin Panel"
admin.site.site_title = "EduGorilla Admin"
admin.site.index_title = "Welcome to EduGorilla Administration"
