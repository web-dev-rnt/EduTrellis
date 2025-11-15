from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

def get_active_smtp_config():
    """Get the active SMTP configuration"""
    try:
        from adminpanel.models import SMTPConfiguration
        return SMTPConfiguration.objects.filter(is_active=True).first()
    except:
        return None

def has_smtp_configured():
    """Check if SMTP is configured and active"""
    return get_active_smtp_config() is not None

def configure_smtp_settings(smtp_config):
    """Temporarily configure Django email settings"""
    if not smtp_config:
        return False
    
    # Store original settings
    original_settings = {}
    email_settings = [
        'EMAIL_BACKEND', 'EMAIL_HOST', 'EMAIL_PORT', 
        'EMAIL_USE_TLS', 'EMAIL_USE_SSL', 'EMAIL_HOST_USER', 
        'EMAIL_HOST_PASSWORD', 'DEFAULT_FROM_EMAIL'
    ]
    
    for setting in email_settings:
        original_settings[setting] = getattr(settings, setting, None)
    
    # Apply SMTP configuration
    settings.EMAIL_BACKEND = smtp_config.email_backend
    settings.EMAIL_HOST = smtp_config.email_host
    settings.EMAIL_PORT = smtp_config.email_port
    settings.EMAIL_USE_TLS = smtp_config.email_use_tls
    settings.EMAIL_USE_SSL = smtp_config.email_use_ssl
    settings.EMAIL_HOST_USER = smtp_config.email_host_user
    settings.EMAIL_HOST_PASSWORD = smtp_config.email_host_password
    settings.DEFAULT_FROM_EMAIL = smtp_config.default_from_email
    
    return original_settings

def restore_smtp_settings(original_settings):
    """Restore original Django email settings"""
    if original_settings:
        for setting, value in original_settings.items():
            setattr(settings, setting, value)

def send_otp_email(user, otp_code):
    """Send OTP verification email"""
    smtp_config = get_active_smtp_config()
    if not smtp_config:
        return False, "No SMTP configuration found"
    
    original_settings = configure_smtp_settings(smtp_config)
    
    try:
        subject = 'Email Verification - OTP Code'
        
        # Create context for email templates
        context = {
            'user': user,
            'otp_code': otp_code,
            'site_name': 'Your Site Name'  # Replace with your site name
        }
        
        # Try to render HTML template, fallback to plain text if template doesn't exist
        try:
            html_message = render_to_string('emails/otp_verification.html', context)
        except:
            html_message = None
        
        # Plain text message
        plain_message = f"""
Hello {user.first_name or user.email},

Your OTP for email verification is: {otp_code}

This OTP will expire in 10 minutes.

If you didn't request this, please ignore this email.

Thanks,
Your Site Team
        """
        
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=smtp_config.default_from_email,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False
        )
        
        return True, "OTP sent successfully"
        
    except Exception as e:
        logger.error(f"Failed to send OTP email: {str(e)}")
        return False, f"Failed to send email: {str(e)}"
    
    finally:
        restore_smtp_settings(original_settings)

def create_and_send_otp(user, verification_type='email'):
    """Create OTP and send via email"""
    from base.models import OTPVerification
    
    # Deactivate previous OTPs
    OTPVerification.objects.filter(
        user=user, 
        verification_type=verification_type
    ).update(is_used=True)
    
    # Create new OTP
    otp = OTPVerification.objects.create(
        user=user,
        verification_type=verification_type
    )
    
    # Send email
    success, message = send_otp_email(user, otp.otp_code)
    
    if not success:
        otp.delete()  # Clean up if email failed
        return None, message
    
    return otp, message
