# base/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from .models import User, OTPVerification, Payment, UserCourseAccess


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ['email']
    list_display = ('email', 'first_name', 'last_name', 'contact_number', 'gender', 'is_staff', 'is_verified', 'is_active', 'date_joined')
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'is_verified', 'gender', 'date_joined')
    search_fields = ('email', 'first_name', 'middle_name', 'last_name', 'contact_number')

    readonly_fields = ('last_login', 'date_joined')

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {
            'fields': (
                'first_name', 'middle_name', 'last_name',
                'age', 'contact_number', 'gender', 'profile_image',
            )
        }),
        (_('Permissions'), {
            'fields': (
                'is_active', 'is_staff', 'is_superuser', 'is_verified',
                'groups', 'user_permissions',
            )
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email', 'password1', 'password2',
                'first_name', 'middle_name', 'last_name',
                'age', 'contact_number', 'gender',
                'is_active', 'is_staff', 'is_verified',
            ),
        }),
    )


@admin.register(OTPVerification)
class OTPVerificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'otp_code', 'verification_type', 'created_at', 'expires_at', 'is_used', 'is_valid')
    list_filter = ('verification_type', 'is_used', 'created_at')
    search_fields = ('user__email', 'otp_code')
    readonly_fields = ('otp_code', 'created_at', 'expires_at', 'is_valid')
    
    fieldsets = (
        (None, {
            'fields': ('user', 'otp_code', 'verification_type')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'expires_at')
        }),
        (_('Status'), {
            'fields': ('is_used', 'is_valid')
        }),
    )
    
    def has_add_permission(self, request):
        # OTP should only be created programmatically
        return False


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('razorpay_order_id', 'user', 'course_name', 'amount_display', 'status', 'created_at')
    list_filter = ('status', 'course_type', 'created_at', 'currency')
    search_fields = ('razorpay_order_id', 'razorpay_payment_id', 'user__email', 'course_name')
    readonly_fields = ('razorpay_order_id', 'razorpay_payment_id', 'razorpay_signature', 'created_at', 'updated_at')
    
    fieldsets = (
        (_('User Info'), {
            'fields': ('user',)
        }),
        (_('Course Details'), {
            'fields': ('course_type', 'course_id', 'course_name')
        }),
        (_('Payment Details'), {
            'fields': ('razorpay_order_id', 'razorpay_payment_id', 'razorpay_signature')
        }),
        (_('Amount & Currency'), {
            'fields': ('amount', 'currency')
        }),
        (_('Status'), {
            'fields': ('status',)
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def amount_display(self, obj):
        """Display amount in rupees"""
        return f"₹{obj.amount / 100:.2f}"
    amount_display.short_description = 'Amount (INR)'


@admin.register(UserCourseAccess)
class UserCourseAccessAdmin(admin.ModelAdmin):
    list_display = ('user', 'course_type', 'course_id', 'is_active', 'has_access', 'is_expired', 'access_granted_at')
    list_filter = ('course_type', 'is_active', 'access_granted_at', 'expires_at')
    search_fields = ('user__email', 'course_id', 'course_type')
    readonly_fields = ('access_granted_at', 'has_access', 'is_expired')
    
    fieldsets = (
        (None, {
            'fields': ('user', 'course_type', 'course_id', 'payment')
        }),
        (_('Access Status'), {
            'fields': ('is_active', 'has_access', 'is_expired')
        }),
        (_('Timestamps'), {
            'fields': ('access_granted_at', 'expires_at')
        }),
    )
