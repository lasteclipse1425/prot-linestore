import re

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError

from .models import Order, Review, UserProfile

User = get_user_model()


class ProfilePhotoForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['photo']
        labels = {
            'photo': 'Фотография профиля',
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
            'username': 'Логин',
            'first_name': 'Имя',
            'last_name': 'Фамилия',
            'email': 'Email',
        }

        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите логин',
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите имя',
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите фамилию',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите email',
            }),
        }


class RegisterForm(forms.Form):
    """Production-safe registration form.

    Validation is intentionally explicit so it can enforce business rules and return
    field-level feedback before a user record is created in the database.
    """

    username = forms.CharField(
        min_length=3,
        max_length=30,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Логин'}),
    )
    first_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Имя'}),
    )
    last_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Фамилия'}),
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'name@example.com'}),
    )
    password1 = forms.CharField(
        min_length=8,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Пароль'}),
    )
    password2 = forms.CharField(
        min_length=8,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Повторите пароль'}),
    )

    def clean_username(self):
        username = self.cleaned_data['username'].strip()
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError('Пользователь с таким логином уже существует.')
        return username

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Пользователь с таким email уже зарегистрирован.')
        return email

    def clean_password1(self):
        password = self.cleaned_data.get('password1', '')
        if len(password) < 8:
            raise forms.ValidationError('Пароль должен содержать не менее 8 символов.')
        if not re.search(r'[A-Z]', password):
            raise forms.ValidationError('Пароль должен содержать хотя бы одну заглавную букву.')
        if not re.search(r'\d', password):
            raise forms.ValidationError('Пароль должен содержать хотя бы одну цифру.')
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
            raise forms.ValidationError('Пароли не совпадают.')

        return cleaned_data


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'text']
        widgets = {
            'text': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Напишите ваше мнение о товаре...'}),
        }
        labels = {
            'rating': 'Оценка',
            'text': 'Ваш отзыв',
        }


class OrderCreateForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ["first_name", "last_name", "email", "address",'quantity']
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ваше имя"}),
            "last_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ваша фамилия"}),
            "email": forms.EmailInput(attrs={"class": "form-control", "placeholder": "Email"}),
            "address": forms.TextInput(attrs={"class": "form-control", "placeholder": "Адрес доставки"}),
            'quantity': forms.NumberInput(attrs={'min': 1, 'style': 'width: 70px;'}),
        }