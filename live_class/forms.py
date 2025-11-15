# live_class/forms.py
from django import forms
from django.forms import inlineformset_factory
from video_courses.models import Category
from .models import LiveClassCourse, LiveClassSession


class LiveClassCourseForm(forms.ModelForm):
    class Meta:
        model = LiveClassCourse
        fields = [
            'name', 'language', 'original_price', 'current_price', 'is_free',
            'banner_image_desktop', 'banner_image_mobile',
            'start_date', 'end_date', 'about', 'category', 'is_active',
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter course name'
            }),
            'language': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., English, Hindi'
            }),
            'original_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'current_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'start_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'end_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'about': forms.Textarea(attrs={
                'rows': 4,
                'class': 'form-control',
                'placeholder': 'Course description...'
            }),
            'category': forms.Select(attrs={
                'class': 'form-control'
            }),
            'banner_image_desktop': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'banner_image_mobile': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
        }
        labels = {
            'name': 'Course Name',
            'language': 'Language',
            'original_price': 'Original Price (₹)',
            'current_price': 'Current Price (₹)',
            'is_free': 'Free Course',
            'banner_image_desktop': 'Desktop Banner',
            'banner_image_mobile': 'Mobile Banner',
            'start_date': 'Start Date',
            'end_date': 'End Date',
            'about': 'About Course',
            'category': 'Category',
            'is_active': 'Active',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make category field display categories from video_courses app
        self.fields['category'].queryset = Category.objects.all().order_by('name')
        self.fields['category'].empty_label = "Select Category"

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        original_price = cleaned_data.get('original_price')
        current_price = cleaned_data.get('current_price')
        is_free = cleaned_data.get('is_free')

        # Validate date range
        if start_date and end_date and start_date >= end_date:
            raise forms.ValidationError("End date must be after start date.")

        # Validate pricing for non-free courses
        if not is_free:
            if original_price and current_price and current_price > original_price:
                raise forms.ValidationError("Current price cannot be higher than original price.")
            if not original_price or not current_price:
                raise forms.ValidationError("Both original and current prices are required for paid courses.")
        else:
            # For free courses, set prices to 0
            cleaned_data['original_price'] = 0
            cleaned_data['current_price'] = 0

        return cleaned_data


class LiveClassSessionForm(forms.ModelForm):
    class Meta:
        model = LiveClassSession
        fields = [
            'class_name', 'subject', 'scheduled_datetime', 
            'duration_minutes', 'max_participants', 
            'is_free', 'enable_auto_recording',
        ]
        widgets = {
            'class_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter class name'
            }),
            'subject': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Class subject/topic'
            }),
            'scheduled_datetime': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-control'
            }),
            'duration_minutes': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '15',
                'max': '480',
                'value': '60'
            }),
            'max_participants': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '500',
                'value': '100'
            }),
        }
        labels = {
            'class_name': 'Class Name',
            'subject': 'Subject/Topic',
            'scheduled_datetime': 'Scheduled Date & Time',
            'duration_minutes': 'Duration (minutes)',
            'max_participants': 'Max Participants',
            'is_free': 'Free Session (Override Course)',
            'enable_auto_recording': 'Enable Recording',
        }

    def clean_scheduled_datetime(self):
        scheduled_datetime = self.cleaned_data.get('scheduled_datetime')
        from django.utils import timezone
        
        if scheduled_datetime and scheduled_datetime <= timezone.now():
            raise forms.ValidationError("Scheduled time must be in the future.")
        
        return scheduled_datetime


# Formset for managing multiple sessions
LiveClassSessionFormSet = inlineformset_factory(
    LiveClassCourse, 
    LiveClassSession, 
    form=LiveClassSessionForm,
    extra=1, 
    can_delete=True,
    min_num=0,
    validate_min=True,
    fk_name='course'
)
