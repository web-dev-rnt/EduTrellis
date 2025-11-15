from django import template
from adminpanel.models import NavbarSettings

register = template.Library()

@register.simple_tag
def get_navbar_settings():
    """Get navbar settings for templates"""
    try:
        return NavbarSettings.objects.first()
    except NavbarSettings.DoesNotExist:
        return None

@register.simple_tag
def get_favicon_url():
    """Get favicon URL directly"""
    try:
        settings = NavbarSettings.objects.first()
        if settings and settings.favicon:
            return settings.favicon.url
        return None
    except:
        return None
