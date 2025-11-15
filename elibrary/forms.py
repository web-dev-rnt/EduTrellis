from django import forms
from django.forms import modelformset_factory
from video_courses.models import Category
from .models import ELibraryCourse, ELibraryPDF


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = [single_file_clean(data, initial)]
        return result


class ELibraryCourseForm(forms.ModelForm):
    class Meta:
        model = ELibraryCourse
        fields = [
            'title', 'short_description', 'description', 'category', 'instructor', 
            'difficulty_level', 'is_free', 'price', 'discount_price', 'cover_image', 
            'preview_pdf', 'total_pages', 'language', 'tags', 
            'is_featured', 'is_active', 'is_bestseller'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Enter course title'}),
            'short_description': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Brief description (max 300 chars)'}),
            'description': forms.Textarea(attrs={'rows': 5, 'placeholder': 'Detailed course description'}),
            'instructor': forms.TextInput(attrs={'placeholder': 'Instructor name'}),
            'price': forms.NumberInput(attrs={'step': '0.01', 'placeholder': '0.00'}),
            'discount_price': forms.NumberInput(attrs={'step': '0.01', 'placeholder': '0.00'}),
            'total_pages': forms.NumberInput(attrs={'placeholder': 'Approximate total pages'}),
            'language': forms.TextInput(attrs={'placeholder': 'e.g., English, Hindi'}),
            'tags': forms.TextInput(attrs={'placeholder': 'Comma-separated tags'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.filter()
        
    def clean(self):
        cleaned_data = super().clean()
        is_free = cleaned_data.get('is_free')
        price = cleaned_data.get('price')
        discount_price = cleaned_data.get('discount_price')
        
        # If not free, price is required
        if not is_free and not price:
            self.add_error('price', 'Price is required for paid courses')
        
        # Validate discount price
        if not is_free and discount_price and price and discount_price >= price:
            self.add_error('discount_price', 'Discount price must be less than regular price')
        
        return cleaned_data


class ELibraryPDFForm(forms.ModelForm):
    class Meta:
        model = ELibraryPDF
        fields = [
            'title', 'description', 'file', 'chapter_number', 
            'order', 'page_count', 'is_preview', 'is_active'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'PDF title'}),
            'description': forms.Textarea(attrs={'rows': 3, 'placeholder': 'PDF description'}),
            'chapter_number': forms.NumberInput(attrs={'min': 1}),
            'order': forms.NumberInput(attrs={'min': 0}),
            'page_count': forms.NumberInput(attrs={'min': 1, 'placeholder': 'Number of pages'}),
        }


class MultiplePDFUploadForm(forms.Form):
    pdfs = MultipleFileField(
        label="PDF Files",
        help_text="Select multiple PDF files (Max 10 files, 50MB each)"
    )
    chapter_number = forms.IntegerField(
        min_value=1, 
        initial=1,
        help_text="Chapter number for all uploaded PDFs"
    )
    auto_title = forms.BooleanField(
        required=False, 
        initial=True,
        help_text="Use filename as PDF title"
    )


# Formset for managing multiple PDFs
ELibraryPDFFormSet = modelformset_factory(
    ELibraryPDF,
    form=ELibraryPDFForm,
    fields=['title', 'description', 'chapter_number', 'order', 'page_count', 'is_preview', 'is_active'],
    extra=0,
    can_delete=True
)
