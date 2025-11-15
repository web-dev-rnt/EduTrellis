from django import forms
from django.forms import inlineformset_factory
from .models import VideoCourse, WhatYouLearnPoint, CourseInclude, CourseVideo, Category


class VideoCourseForm(forms.ModelForm):
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        required=True,
        label="Category"
    )
    
    class Meta:
        model = VideoCourse
        fields = [
            "name", "category",
            "description", "thumbnail",
            "original_price", "selling_price", "currency",
            "is_premium", "is_free", "is_bestseller",
            "rating", "rating_count", "total_hours",
            # Instructor moved to bottom in template layout (fields still here)
            "instructor_name", "instructor_headline", "instructor_avatar",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 5, "placeholder": "Describe the course..."}),
        }
        help_texts = {
            "is_free": "Check this box to make the course free. Selling price will be set to 0 automatically.",
            "is_premium": "Premium courses have special features or higher quality content.",
        }
    
    def clean(self):
        cleaned_data = super().clean()
        is_free = cleaned_data.get('is_free')
        selling_price = cleaned_data.get('selling_price')
        
        # If marked as free, ensure selling price is 0
        if is_free and selling_price and selling_price > 0:
            cleaned_data['selling_price'] = 0
        
        # If not free and selling price is 0, warn user
        if not is_free and selling_price == 0:
            self.add_error('is_free', 'Selling price is 0. Consider marking this course as free.')
        
        return cleaned_data


LearnFormSet = inlineformset_factory(
    VideoCourse, WhatYouLearnPoint,
    fields=["text"],
    extra=3, can_delete=True
)


IncludeFormSet = inlineformset_factory(
    VideoCourse, CourseInclude,
    fields=["label"],
    extra=3, can_delete=True
)


VideoFormSet = inlineformset_factory(
    VideoCourse, CourseVideo,
    fields=["title", "is_preview", "file", "thumb_image"],
    extra=2, can_delete=True
)
