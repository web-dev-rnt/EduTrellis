# adminpanel/context_processors.py
from .models import NavbarSettings, FooterSettings, FooterLink, FooterLegalLink
from video_courses.models import Category

def navbar_settings(request):
    """Make navbar settings available in all templates"""
    try:
        settings = NavbarSettings.objects.filter(is_active=True).first()
        if not settings:
            settings = NavbarSettings.objects.create()
        return {'navbar_settings': settings}
    except Exception as e:
        print(f"Error in navbar_settings context processor: {e}")
        return {'navbar_settings': None}

def footer_settings(request):
    """Make footer settings available in all templates"""
    try:
        settings = FooterSettings.objects.filter(is_active=True).first()
        footer_links = FooterLink.objects.filter(is_active=True)
        footer_legal_links = FooterLegalLink.objects.filter(is_active=True)
        
        if not settings:
            settings = FooterSettings.objects.create()
        
        return {
            'footer_settings': settings,
            'footer_links': footer_links,
            'footer_legal_links': footer_legal_links,
        }
    except Exception as e:
        print(f"Error in footer_settings context processor: {e}")
        return {
            'footer_settings': None,
            'footer_links': [],
            'footer_legal_links': [],
        }
