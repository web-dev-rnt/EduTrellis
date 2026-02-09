# adminpanel/forms.py
from django import forms  # noqa: F401  (forms used throughout)
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from .models import (
    Coupon,
    Banner,
    StatCard,
    CTASection,
    AboutUsSection,
    WhyChooseUsItem,
    ServiceItem,
    NavbarSettings,
    FooterSettings,
    FooterLink,
    FooterLegalLink,
    DeveloperPopup,
    Notification,
)

User = get_user_model()

# Notifications
class NotificationForm(forms.ModelForm):
    class Meta:
        model = Notification
        fields = ['title', 'body', 'link']  # Removed is_active
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter notification title',
                'maxlength': '200'
            }),
            'body': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Enter notification message',
                'rows': 5
            }),
            'link': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://example.com (optional)'
            })
        }
        
    def clean_title(self):
        title = self.cleaned_data.get('title')
        if not title or not title.strip():
            raise forms.ValidationError("Title cannot be empty")
        return title.strip()
    
    def clean_body(self):
        body = self.cleaned_data.get('body')
        if not body or not body.strip():
            raise forms.ValidationError("Message body cannot be empty")
        return body.strip()

class DeveloperPopupForm(forms.ModelForm):
    class Meta:
        model = DeveloperPopup
        fields = [
            'profile_image', 'greeting_text', 'developer_name', 'tagline',
            'message_title', 'message_body', 'email', 'whatsapp_number',
            'linkedin_url', 'linkedin_display_text', 'footer_message',
            'is_active', 'delay_seconds', 'show_once_per_session'
        ]
        widgets = {
            'greeting_text': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Greetings! I\'m'
            }),
            'developer_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., John Doe'
            }),
            'tagline': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Brief description about yourself and your work...'
            }),
            'message_title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., I design professional websites!'
            }),
            'message_body': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Your service description...'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'your@email.com'
            }),
            'whatsapp_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '917905817391'
            }),
            'linkedin_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://www.linkedin.com/in/username/'
            }),
            'linkedin_display_text': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your Name'
            }),
            'footer_message': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 🚀 Looking forward to working with all of you!'
            }),
            'delay_seconds': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '30'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'show_once_per_session': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
    
    def clean_profile_image(self):
        image = self.cleaned_data.get('profile_image')
        if image:
            # Check file size (max 1MB)
            if image.size > 1 * 1024 * 1024:
                raise forms.ValidationError("Image file size cannot exceed 1MB.")
        return image
    
    def clean_whatsapp_number(self):
        number = self.cleaned_data.get('whatsapp_number')
        # Remove any spaces or special characters except +
        cleaned_number = ''.join(filter(str.isdigit, number))
        return cleaned_number


class CouponForm(forms.ModelForm):
    class Meta:
        model = Coupon
        fields = [
            'code',
            'description',
            'discount_type',
            'discount_value',
            'usage_limit',
            'valid_from',
            'valid_to',
            'minimum_amount',
            'maximum_discount',
            'status',
        ]
        widgets = {
            'code': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Enter coupon code',
                    'style': 'text-transform: uppercase;',
                }
            ),
            'description': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 3,
                    'placeholder': 'Describe this coupon...',
                }
            ),
            'discount_type': forms.Select(attrs={'class': 'form-control'}),
            'discount_value': forms.NumberInput(
                attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}
            ),
            'usage_limit': forms.NumberInput(
                attrs={'class': 'form-control', 'min': '1'}
            ),
            'valid_from': forms.DateTimeInput(
                attrs={'class': 'form-control', 'type': 'datetime-local'}
            ),
            'valid_to': forms.DateTimeInput(
                attrs={'class': 'form-control', 'type': 'datetime-local'}
            ),
            'minimum_amount': forms.NumberInput(
                attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}
            ),
            'maximum_discount': forms.NumberInput(
                attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}
            ),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set sensible defaults for new instances
        if not self.instance.pk:
            now = timezone.localtime()
            self.fields['valid_from'].initial = now
            self.fields['valid_to'].initial = now + timezone.timedelta(days=30)

    def clean(self):
        cleaned_data = super().clean()
        valid_from = cleaned_data.get('valid_from')
        valid_to = cleaned_data.get('valid_to')
        discount_value = cleaned_data.get('discount_value')
        discount_type = cleaned_data.get('discount_type')

        if valid_from and valid_to and valid_from >= valid_to:
            raise ValidationError('Valid to date must be after valid from date.')

        if discount_type == 'percentage' and discount_value and discount_value > 100:
            raise ValidationError('Percentage discount cannot be more than 100%.')

        return cleaned_data

    def clean_code(self):
        code = (self.cleaned_data.get('code') or '').upper().strip()
        if code:
            qs = Coupon.objects.filter(code=code)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError('A coupon with this code already exists.')
        return code


class CouponApplyForm(forms.Form):
    """Form for customers to apply coupons"""
    code = forms.CharField(
        max_length=50,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Enter coupon code',
                'style': 'text-transform: uppercase;',
            }
        ),
    )

    def clean_code(self):
        code = (self.cleaned_data.get('code') or '').upper().strip()
        if not code:
            raise ValidationError('Please enter a coupon code.')
        return code


class BannerForm(forms.ModelForm):
    class Meta:
        model = Banner
        fields = ['title', 'image', 'alt_text', 'link_url', 'is_active', 'order']
        widgets = {
            'title': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'Banner Title'}
            ),
            'image': forms.ClearableFileInput(
                attrs={'class': 'form-control', 'accept': 'image/*'}
            ),
            'alt_text': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Descriptive text for the image',
                }
            ),
            'link_url': forms.URLInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'https://example.com (optional)',
                }
            ),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['image'].help_text = (
            'Recommended size: 1920x800px for best results'
        )


class StatCardForm(forms.ModelForm):
    class Meta:
        model = StatCard
        fields = ['icon_type', 'icon', 'icon_image', 'icon_color', 'number', 'label', 'is_active', 'order']
        widgets = {
            'icon_type': forms.Select(
                attrs={
                    'class': 'form-control',
                    'id': 'icon-type-select'
                }
            ),
            'icon': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'users, graduation-cap, book, etc.',
                    'maxlength': '50',
                }
            ),
            'icon_image': forms.ClearableFileInput(
                attrs={
                    'class': 'form-control',
                    'accept': 'image/*'
                }
            ),
            'icon_color': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'type': 'color',
                    'value': '#007bff'
                }
            ),
            'number': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': '4 Crore+'}
            ),
            'label': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'Users'}
            ),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add help text for file upload
        self.fields['icon_image'].help_text = "Upload PNG, JPG, or SVG image (max 2MB)"
        self.fields['icon'].help_text = "Enter Font Awesome icon name without 'fa-' prefix"
        self.fields['icon_color'].help_text = "Color for Font Awesome icons"


class CTASectionForm(forms.ModelForm):
    class Meta:
        model = CTASection
        fields = ['title', 'button_text', 'button_link', 'is_active']
        widgets = {
            'title': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Increase Selection Chances by 16X',
                }
            ),
            'button_text': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'Perform | Analyse | Improve'}
            ),
            'button_link': forms.URLInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'https://example.com (optional)',
                }
            ),
        }


class AboutUsSectionForm(forms.ModelForm):
    class Meta:
        model = AboutUsSection
        fields = [
            'company_name',
            'heading',
            'description',
            'logo',
            'address',
            'email',
            'phone',
            'phone_hours',
            'facebook_url',
            'twitter_url',
            'linkedin_url',
            'instagram_url',
            'telegram_url',
            'map_embed_url',
            'is_active',
        ]
        widgets = {
            'company_name': forms.TextInput(attrs={'class': 'form-control'}),
            'heading': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'logo': forms.ClearableFileInput(
                attrs={'class': 'form-control', 'accept': 'image/*'}
            ),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_hours': forms.TextInput(attrs={'class': 'form-control'}),
            'facebook_url': forms.URLInput(attrs={'class': 'form-control'}),
            'twitter_url': forms.URLInput(attrs={'class': 'form-control'}),
            'linkedin_url': forms.URLInput(attrs={'class': 'form-control'}),
            'instagram_url': forms.URLInput(attrs={'class': 'form-control'}),
            'telegram_url': forms.URLInput(attrs={'class': 'form-control'}),
            'map_embed_url': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class WhyChooseUsItemForm(forms.ModelForm):
    class Meta:
        model = WhyChooseUsItem
        fields = ['icon_class', 'title', 'description', 'is_active', 'order']
        widgets = {
            'icon_class': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'fa fa-user-circle'}
            ),
            'title': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Trusted by 4+ crore learners',
                }
            ),
            'description': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Description text...'}
            ),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
        }


class ServiceItemForm(forms.ModelForm):
    class Meta:
        model = ServiceItem
        fields = ['icon_class', 'service_name', 'service_description', 'is_active', 'order']
        widgets = {
            'icon_class': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'fa fa-video-camera'}
            ),
            'service_name': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Live & Interactive Classes',
                }
            ),
            'service_description': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Service description...'}
            ),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
        }

class NavbarSettingsForm(forms.ModelForm):
    class Meta:
        model = NavbarSettings
        fields = ['logo', 'favicon', 'contact_number', 'contact_hours', 'contact_type', 'search_placeholder', 'is_active']
        widgets = {
            'logo': forms.ClearableFileInput(
                attrs={'class': 'form-control', 'accept': 'image/*'}
            ),
            'favicon': forms.ClearableFileInput(
                attrs={'class': 'form-control', 'accept': 'image/x-icon,image/png,image/jpeg'}
            ),
            'contact_number': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': '7905817391'}
            ),
            'contact_hours': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': '(10 AM to 7 PM)'}
            ),
            'contact_type': forms.Select(
                attrs={'class': 'form-control'}
            ),
            'search_placeholder': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'Search courses'}
            ),
        }
        labels = {
            'logo': 'Website Logo',
            'favicon': 'Website Favicon',
            'contact_number': 'Contact Number',
            'contact_hours': 'Contact Hours',
            'contact_type': 'Contact Method',
            'search_placeholder': 'Search Placeholder Text',
            'is_active': 'Active',
        }
        help_texts = {
            'logo': 'Upload PNG/JPG logo (recommended size: 200x60px)',
            'favicon': 'Upload favicon (16x16 or 32x32 px, .ico, .png, or .jpg format)',
            'contact_number': 'Enter 10-digit mobile number (without +91)',
            'contact_type': 'Choose WhatsApp or Phone Call',
        }



class FooterSettingsForm(forms.ModelForm):
    class Meta:
        model = FooterSettings
        fields = [
            'logo',
            'email',
            'copyright_text',
            'google_play_url',
            'app_store_url',
            'facebook_url',
            'twitter_url',
            'youtube_url',
            'linkedin_url',
            'instagram_url',
            'telegram_url',
            'is_active',
        ]
        widgets = {
            'logo': forms.ClearableFileInput(
                attrs={'class': 'form-control', 'accept': 'image/*'}
            ),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'copyright_text': forms.TextInput(attrs={'class': 'form-control'}),
            'google_play_url': forms.URLInput(attrs={'class': 'form-control'}),
            'app_store_url': forms.URLInput(attrs={'class': 'form-control'}),
            'facebook_url': forms.URLInput(attrs={'class': 'form-control'}),
            'twitter_url': forms.URLInput(attrs={'class': 'form-control'}),
            'youtube_url': forms.URLInput(attrs={'class': 'form-control'}),
            'linkedin_url': forms.URLInput(attrs={'class': 'form-control'}),
            'instagram_url': forms.URLInput(attrs={'class': 'form-control'}),
            'telegram_url': forms.URLInput(attrs={'class': 'form-control'}),
        }


class FooterLinkForm(forms.ModelForm):
    class Meta:
        model = FooterLink
        fields = ['section', 'title', 'url', 'order', 'is_active']
        widgets = {
            'section': forms.Select(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'url': forms.TextInput(attrs={'class': 'form-control'}),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
        }


class FooterLegalLinkForm(forms.ModelForm):
    class Meta:
        model = FooterLegalLink
        fields = ['title', 'url', 'order', 'is_active']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'url': forms.TextInput(attrs={'class': 'form-control'}),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
        }



class AdminCreateUserForm(forms.ModelForm):
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'placeholder': 'Password'}),
        strip=False,
    )
    confirm_password = forms.CharField(
        label='Confirm password',
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirm password'}),
        strip=False,
    )

    class Meta:
        model = User
        fields = [
            'first_name',
            'middle_name',
            'last_name',
            'age',
            'contact_number',
            'gender',
            'email',
            'profile_image',
            'is_staff',
            'is_superuser',
            'is_active',
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'placeholder': 'First name'}),
            'middle_name': forms.TextInput(attrs={'placeholder': 'Middle name'}),
            'last_name': forms.TextInput(attrs={'placeholder': 'Last name'}),
            'age': forms.NumberInput(attrs={'min': 1, 'max': 120, 'placeholder': 'Age'}),
            'contact_number': forms.TextInput(
                attrs={'placeholder': 'Contact number', 'inputmode': 'tel'}
            ),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'email': forms.EmailInput(
                attrs={'placeholder': 'Email', 'autocomplete': 'email'}
            ),
            'profile_image': forms.ClearableFileInput(attrs={'accept': 'image/*'}),
        }

    def clean(self):
        cleaned = super().clean()
        pwd = cleaned.get('password')
        cpwd = cleaned.get('confirm_password')
        if pwd and cpwd and pwd != cpwd:
            self.add_error('confirm_password', 'Passwords do not match.')
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get('password')
        if password:
            user.set_password(password)
        if commit:
            user.save()
        return user
        
# bundles/forms.py
from django import forms
from .models import ProductBundle
from video_courses.models import VideoCourse, Category
from live_class.models import LiveClassCourse
from testseries.models import TestSeries
from elibrary.models import ELibraryCourse


class ProductBundleForm(forms.ModelForm):
    """Form for creating and editing product bundles"""
    
    class Meta:
        model = ProductBundle
        fields = [
            'title', 'description', 'short_description', 'bundle_type', 'category',
            'thumbnail', 'banner_image', 'is_free', 'original_price', 'bundle_price', 'currency',
            'video_courses', 'live_classes', 'test_series', 'elibrary_courses',
            'features', 'validity_days', 'start_date', 'end_date',
            'status', 'is_featured', 'is_bestseller', 'is_trending',
            'display_order', 'max_enrollments'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter bundle title'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Detailed description of the bundle...'
            }),
            'short_description': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Brief description for card view'
            }),
            'bundle_type': forms.Select(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'thumbnail': forms.FileInput(attrs={'class': 'form-control'}),
            'banner_image': forms.FileInput(attrs={'class': 'form-control'}),
            'is_free': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'id': 'id_is_free',
                'onchange': 'togglePricing(this)'
            }),
            'original_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'id': 'id_original_price'
            }),
            'bundle_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'id': 'id_bundle_price'
            }),
            'currency': forms.TextInput(attrs={'class': 'form-control'}),
            'video_courses': forms.CheckboxSelectMultiple(),
            'live_classes': forms.CheckboxSelectMultiple(),
            'test_series': forms.CheckboxSelectMultiple(),
            'elibrary_courses': forms.CheckboxSelectMultiple(),
            'features': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Enter one feature per line:\n- Feature 1\n- Feature 2\n- Feature 3'
            }),
            'validity_days': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1'
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_bestseller': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_trending': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'display_order': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0'
            }),
            'max_enrollments': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Make some fields optional
        self.fields['short_description'].required = False
        self.fields['category'].required = False
        self.fields['thumbnail'].required = False
        self.fields['banner_image'].required = False
        self.fields['features'].required = False
        self.fields['start_date'].required = False
        self.fields['end_date'].required = False
        self.fields['max_enrollments'].required = False
        
        # Make pricing fields optional (will be validated in clean method)
        self.fields['original_price'].required = False
        self.fields['bundle_price'].required = False
        
        # Add help text
        self.fields['is_free'].help_text = "If checked, bundle will be free and prices will be set to 0"
        self.fields['original_price'].help_text = "Click 'Auto-Calculate' button to calculate from selected products"
        self.fields['bundle_price'].help_text = "Set your discounted bundle price"
    
    def clean(self):
        cleaned_data = super().clean()
        is_free = cleaned_data.get('is_free')
        bundle_price = cleaned_data.get('bundle_price')
        original_price = cleaned_data.get('original_price')
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        # If bundle is free, set prices to 0
        if is_free:
            cleaned_data['original_price'] = 0
            cleaned_data['bundle_price'] = 0
        else:
            # For paid bundles, ensure prices are provided
            if original_price is None or original_price == '':
                raise forms.ValidationError({
                    'original_price': 'Original price is required for paid bundles.'
                })
            
            if bundle_price is None or bundle_price == '':
                raise forms.ValidationError({
                    'bundle_price': 'Bundle price is required for paid bundles.'
                })
            
            # Convert to Decimal for comparison
            original_price = cleaned_data.get('original_price', 0)
            bundle_price = cleaned_data.get('bundle_price', 0)
            
            # Validate bundle price is less than original for paid bundles
            if bundle_price and original_price:
                if bundle_price >= original_price:
                    raise forms.ValidationError(
                        "Bundle price must be less than original price to offer a discount."
                    )
        
        # Validate dates
        if start_date and end_date:
            if end_date <= start_date:
                raise forms.ValidationError(
                    "End date must be after start date."
                )
        
        # Validate at least one product is selected
        video_courses = cleaned_data.get('video_courses')
        live_classes = cleaned_data.get('live_classes')
        test_series = cleaned_data.get('test_series')
        elibrary_courses = cleaned_data.get('elibrary_courses')
        
        has_products = bool(
            video_courses or live_classes or test_series or elibrary_courses
        )
        
        if not has_products:
            raise forms.ValidationError(
                "Please select at least one product for the bundle."
            )
        
        return cleaned_data


class BundleFilterForm(forms.Form):
    """Form for filtering bundles in admin panel"""
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search bundles...'
        })
    )
    
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        required=False,
        empty_label="All Categories",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    bundle_type = forms.ChoiceField(
        choices=[('', 'All Types')] + ProductBundle.BUNDLE_TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    status = forms.ChoiceField(
        choices=[('', 'All Status')] + ProductBundle.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    is_featured = forms.NullBooleanField(
        required=False,
        widget=forms.Select(
            choices=[('', 'All'), ('true', 'Featured'), ('false', 'Not Featured')],
            attrs={'class': 'form-control'}
        )
    )
    
    is_free = forms.NullBooleanField(
        required=False,
        widget=forms.Select(
            choices=[('', 'All Bundles'), ('true', 'Free Only'), ('false', 'Paid Only')],
            attrs={'class': 'form-control'}
        )
    )