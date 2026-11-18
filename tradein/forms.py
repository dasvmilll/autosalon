from django import forms
from django.core.exceptions import ValidationError
from .models import TradeInRequest
import re

class TradeInRequestForm(forms.ModelForm):
    phone = forms.CharField(
        max_length=20, 
        required=True, 
        widget=forms.TextInput(attrs={'placeholder': '+7 900 000-00-00', 'class': 'form-control'})
    )

    class Meta:
        model = TradeInRequest
        fields = ['brand', 'model_name', 'year', 'mileage_km', 'photo']
        widgets = {
            'brand': forms.TextInput(attrs={'class': 'form-control'}),
            'model_name': forms.TextInput(attrs={'class': 'form-control'}),
            'year': forms.NumberInput(attrs={'class': 'form-control'}),
            'mileage_km': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def clean_year(self):
        year = self.cleaned_data.get('year')
        if year < 1900 or year > 2026:
            raise ValidationError('Введите корректный год выпуска (от 1900 до 2026).')
        return year

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        # Простая проверка формата: +7 и 10 цифр
        if not re.match(r'^\+7\s?\d{3}\s?\d{3}[-\s]?\d{2}[-\s]?\d{2}$', phone):
            raise ValidationError('Введите телефон в формате +7 900 000-00-00.')
        return phone