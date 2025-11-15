from django import template
from adminpanel.models import *

register = template.Library()

@register.inclusion_tag('components/banner_slider.html')
def render_banner_slider():
    banners = Banner.objects.filter(is_active=True)
    return {'banners': banners}


@register.inclusion_tag('components/stats_section.html')
def render_stats_section():
    stat_cards = StatCard.objects.filter(is_active=True).order_by('order')
    return {'stat_cards': stat_cards}

@register.inclusion_tag('components/cta_section.html')
def render_cta_section():
    cta_sections = CTASection.objects.filter(is_active=True)
    return {'cta_sections': cta_sections}

@register.inclusion_tag('components/about_us_section.html')
def render_about_us_section():
    about_us = AboutUsSection.objects.filter(is_active=True).first()
    why_choose_items = WhyChooseUsItem.objects.filter(is_active=True)
    service_items = ServiceItem.objects.filter(is_active=True)
    
    return {
        'about_us': about_us,
        'why_choose_items': why_choose_items,
        'service_items': service_items,
    }

@register.inclusion_tag('components/footer_section.html')
def render_footer_section():
    footer_settings = FooterSettings.objects.filter(is_active=True).first()
    footer_links = FooterLink.objects.filter(is_active=True)
    footer_legal_links = FooterLegalLink.objects.filter(is_active=True)
    
    # Define footer sections for template
    footer_sections = [
        ('about', 'About'),
        ('help', 'Help'),
        ('student', 'Student'),
        ('business', 'Business'),
    ]
    
    return {
        'footer_settings': footer_settings,
        'footer_links': footer_links,
        'footer_legal_links': footer_legal_links,
        'footer_sections': footer_sections,
    }