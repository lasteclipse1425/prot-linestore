from django import forms
from .models import Order, Review, UserProfile
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model


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


User = get_user_model()


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


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = [
            'username',
            'email',
            'password1',
            'password2',
        ]
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