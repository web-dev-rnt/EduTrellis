from django import template
from adminpanel.models import DeveloperPopup

register = template.Library()

@register.inclusion_tag('developer_popup_partial.html')
def render_developer_popup():
    """Render the developer popup only if active configuration exists"""
    try:
        popup = DeveloperPopup.objects.filter(is_active=True).first()
    except:
        popup = None
    
    return {
        'popup': popup,
        'show_popup': popup is not None  # Explicit flag for rendering
    }
