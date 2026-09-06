from .models import PWASettings


def context_processor(request):
    """Makes share-preview and favicon customization available site-wide."""
    return {'site_customization': PWASettings.get_solo()}
