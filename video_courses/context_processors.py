from .models import Category

def categories_context(request):
    """Context processor to make categories available in all templates"""
    categories = Category.objects.all()
    return {
        'navbar_categories': categories
    }
