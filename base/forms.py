# base/forms.py
from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

User = get_user_model()

class EmailLoginForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)



class SignupForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Password', 
            'autocomplete': 'new-password',
            'class': 'form-input'
        }),
        strip=False
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Confirm Password', 
            'autocomplete': 'new-password',
            'class': 'form-input'
        }),
        strip=False
    )

    class Meta:
        model = User
        fields = [
            'first_name', 'middle_name', 'last_name',
            'age', 'gender', 'contact_number',
            'email', 'profile_image',
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={
                'placeholder': 'First Name *', 
                'class': 'form-input'
            }),
            'middle_name': forms.TextInput(attrs={
                'placeholder': 'Middle Name', 
                'class': 'form-input'
            }),
            'last_name': forms.TextInput(attrs={
                'placeholder': 'Last Name *', 
                'class': 'form-input'
            }),
            'age': forms.NumberInput(attrs={
                'placeholder': 'Age *', 
                'min': 1, 
                'max': 120,
                'class': 'form-input'
            }),
            'gender': forms.Select(attrs={
                'class': 'form-input'
            }),
            'contact_number': forms.TextInput(attrs={
                'placeholder': 'Contact Number *', 
                'inputmode': 'tel',
                'class': 'form-input'
            }),
            'email': forms.EmailInput(attrs={
                'placeholder': 'Email Address *', 
                'autocomplete': 'email',
                'class': 'form-input'
            }),
            'profile_image': forms.FileInput(attrs={
                'class': 'form-input-file',
                'accept': 'image/*'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set required fields
        self.fields['first_name'].required = True
        self.fields['middle_name'].required = False
        self.fields['last_name'].required = True
        self.fields['age'].required = True
        self.fields['gender'].required = True
        self.fields['contact_number'].required = True
        self.fields['email'].required = True
        self.fields['profile_image'].required = False
        
        # Update gender field empty label
        self.fields['gender'].empty_label = 'Select Gender *'

    def clean_age(self):
        age = self.cleaned_data.get('age')
        if age is None:
            raise ValidationError('Age is required.')
        if not (1 <= age <= 120):
            raise ValidationError('Please enter a valid age between 1 and 120.')
        return age

    def clean_contact_number(self):
        contact = self.cleaned_data.get('contact_number')
        if contact and len(contact) < 10:
            raise ValidationError('Please enter a valid contact number.')
        return contact

    def clean_profile_image(self):
        image = self.cleaned_data.get('profile_image')
        if image:
            # Validate file size (max 5MB)
            if image.size > 5 * 1024 * 1024:
                raise ValidationError('Image file size should not exceed 5MB.')
            # Validate file type
            if not image.content_type.startswith('image/'):
                raise ValidationError('Please upload a valid image file.')
        return image

    def clean(self):
        cleaned = super().clean()
        pwd = cleaned.get('password')
        cpwd = cleaned.get('confirm_password')
        if pwd and cpwd and pwd != cpwd:
            self.add_error('confirm_password', 'Passwords do not match.')
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user


class OTPVerificationForm(forms.Form):
    otp_code = forms.CharField(
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter 6-digit OTP',
            'class': 'form-control otp-input',
            'pattern': '[0-9]{6}',
            'title': 'Please enter a 6-digit OTP',
            'autocomplete': 'one-time-code',
            'inputmode': 'numeric'
        })
    )
    def __init__(self, user=None, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_otp_code(self):
        otp_code = self.cleaned_data.get('otp_code')
        if not otp_code or not otp_code.isdigit() or len(otp_code) != 6:
            raise forms.ValidationError('Please enter a valid 6-digit OTP.')
        if self.user:
            from base.models import OTPVerification
            otp = OTPVerification.objects.filter(
                user=self.user,
                otp_code=otp_code,
                verification_type='email'
            ).first()
            if not otp:
                raise forms.ValidationError('Invalid OTP code.')
            if not otp.is_valid():
                raise forms.ValidationError('OTP has expired. Please request a new one.')
        return otp_code

class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = [
            'first_name', 'middle_name', 'last_name',
            'age', 'gender', 'contact_number',
            'email', 'profile_image'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-input', 
                'placeholder': 'First Name *'
            }),
            'middle_name': forms.TextInput(attrs={
                'class': 'form-input', 
                'placeholder': 'Middle Name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-input', 
                'placeholder': 'Last Name *'
            }),
            'age': forms.NumberInput(attrs={
                'class': 'form-input', 
                'min': 1, 
                'max': 120, 
                'placeholder': 'Age *'
            }),
            'gender': forms.Select(attrs={
                'class': 'form-input'
            }),
            'contact_number': forms.TextInput(attrs={
                'class': 'form-input', 
                'inputmode': 'tel', 
                'placeholder': 'Contact Number *'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-input', 
                'placeholder': 'Email Address *', 
                'autocomplete': 'email'
            }),
            'profile_image': forms.FileInput(attrs={
                'id': 'id_profile_image',
                'class': 'file-hidden-input',
                'accept': 'image/*'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set required fields
        self.fields['first_name'].required = True
        self.fields['middle_name'].required = False
        self.fields['last_name'].required = True
        self.fields['age'].required = True
        self.fields['gender'].required = True
        self.fields['contact_number'].required = True
        self.fields['email'].required = True
        self.fields['profile_image'].required = False
        
        # Update gender field empty label
        self.fields['gender'].empty_label = 'Select Gender *'

    def clean_age(self):
        age = self.cleaned_data.get('age')
        if age is None:
            raise ValidationError('Age is required.')
        if not (1 <= age <= 120):
            raise ValidationError('Please enter a valid age between 1 and 120.')
        return age

    def clean_contact_number(self):
        contact = self.cleaned_data.get('contact_number')
        if contact and len(contact) < 10:
            raise ValidationError('Please enter a valid contact number (at least 10 digits).')
        return contact

    def clean_profile_image(self):
        image = self.cleaned_data.get('profile_image')
        if image:
            # Validate file size (max 5MB)
            if hasattr(image, 'size') and image.size > 5 * 1024 * 1024:
                raise ValidationError('Image file size should not exceed 5MB.')
            # Validate file type
            if hasattr(image, 'content_type') and not image.content_type.startswith('image/'):
                raise ValidationError('Please upload a valid image file.')
        return image

# NEW: Simple password change form
class PasswordChangeSimpleForm(forms.Form):
    old_password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Current password', 'autocomplete': 'current-password'}))
    new_password1 = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'New password', 'autocomplete': 'new-password'}))
    new_password2 = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Confirm new password', 'autocomplete': 'new-password'}))

    def clean(self):
        cleaned = super().clean()
        new1 = cleaned.get('new_password1')
        new2 = cleaned.get('new_password2')
        if new1 and new2 and new1 != new2:
            self.add_error('new_password2', 'Passwords do not match.')
        if new1 and len(new1) < 8:
            self.add_error('new_password1', 'Password must be at least 8 characters.')
        return cleaned
