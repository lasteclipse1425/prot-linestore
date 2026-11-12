import re

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _

from .models import Order, Review, UserProfile

User = get_user_model()


class ProfilePhotoForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['photo']
        labels = {
            'photo': _('Profile photo'),
        }
        widgets = {
            'photo': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
            }),
        }


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']

        labels = {
            'username': _('Username'),
            'first_name': _('First name'),
            'last_name': _('Last name'),
            'email': 'Email',
        }

        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Enter username'),
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Enter first name'),
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Enter last name'),
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': _('Enter email'),
            }),
        }


class RegisterForm(forms.Form):
    """Production-safe registration form.

    Validation is intentionally explicit so it can enforce business rules and return
    field-level feedback before a user record is created in the database.
    """

    username = forms.CharField(
        label=_('Username'),
        min_length=3,
        max_length=30,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Username')}),
    )
    first_name = forms.CharField(
        label=_('First name'),
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('First name')}),
    )
    last_name = forms.CharField(
        label=_('Last name'),
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Last name')}),
    )
    email = forms.EmailField(
        label=_('Email'),
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'name@example.com'}),
    )
    password1 = forms.CharField(
        label=_('Password'),
        min_length=8,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': _('Password')}),
    )
    password2 = forms.CharField(
        label=_('Confirm password'),
        min_length=8,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': _('Confirm password')}),
    )

    def clean_username(self):
        username = self.cleaned_data['username'].strip()
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError(_('An account with this username already exists.'))
        return username

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(_('An account with this email is already registered.'))
        return email

    def clean_password1(self):
        password = self.cleaned_data.get('password1', '')
        if len(password) < 8:
            raise forms.ValidationError(_('Password must be at least 8 characters long.'))
        if not re.search(r'[A-Z]', password):
            raise forms.ValidationError(_('Password must include at least one uppercase letter.'))
        if not re.search(r'\d', password):
            raise forms.ValidationError(_('Password must include at least one number.'))
        user = User(
            username=self.data.get('username', '').strip(),
            email=self.data.get('email', '').strip(),
        )
        try:
            validate_password(password, user=user)
        except DjangoValidationError as error:
            raise forms.ValidationError(error.messages) from error
        return password

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError(_('Passwords do not match.'))

        return cleaned_data


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'text']
        widgets = {
            'text': forms.Textarea(attrs={'rows': 4, 'placeholder': _('Share your feedback about this product.')}),
        }
        labels = {
            'rating': _('Rating'),
            'text': _('Your review'),
        }


class OrderCreateForm(forms.ModelForm):
    quantity = forms.IntegerField(
        min_value=1,
        validators=[MinValueValidator(1)],
        widget=forms.NumberInput(attrs={'min': 1, 'class': 'form-control'}),
    )

    class Meta:
        model = Order
        fields = ["first_name", "last_name", "email", "address",'quantity']
        labels = {
            'first_name': _('First name'),
            'last_name': _('Last name'),
            'email': _('Email'),
            'address': _('Delivery address'),
            'quantity': _('Quantity'),
        }
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-control", "placeholder": _('First name')}),
            "last_name": forms.TextInput(attrs={"class": "form-control", "placeholder": _('Last name')}),
            "email": forms.EmailInput(attrs={"class": "form-control", "placeholder": _('Email')}),
            "address": forms.TextInput(attrs={"class": "form-control", "placeholder": _('Delivery address')}),
            'quantity': forms.NumberInput(attrs={'min': 1, 'class': 'form-control'}),
        }
