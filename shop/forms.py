from dataclasses import field
from random import choice, choices

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.forms import widgets
from django.forms.widgets import Textarea
from .models import Rating,Order

class RegistrationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email", "password1", "password2"]

class RatingForm(forms.ModelForm):
    class Meta:
        model = Rating
        fields = ['rating','comment']
        widgets = {
            'rating': forms.Select(choices=[(i, i) for i in range(1, 6)]),
            'comment': forms.Textarea(attrs={'rows': 4})
        }

class CheckoutForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ["first_name", "last_name", "email","address","postal_code","city","note"]

