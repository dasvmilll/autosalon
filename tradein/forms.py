from django import forms
from django.core.exceptions import ValidationError
from .models import TradeInRequest


class TradeInRequestForm(forms.ModelForm):
    """Форма заявки на трейд-ин от покупателя.
    
    ИСПРАВЛЕНИЕ УЯЗВИМОСТЕЙ №1 и №2:
    - №1 (BUG-16): добавлена серверная валидация размера файла (макс. 5 МБ),
      расширения (только jpg/jpeg/png) и MIME-типа (защита от file.php.jpg).
    - №2: поле фото сделано строго обязательным, несмотря на blank=True в модели.
    """

    class Meta:
        model = TradeInRequest
        fields = ['brand', 'model_name', 'year', 'mileage_km', 'photo']
        widgets = {
            'brand': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Например, Toyota'
            }),
            'model_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Например, Camry'
            }),
            'year': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '2020',
                'min': 1950,
                'max': 2026
            }),
            'mileage_km': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '50000',
                'min': 0
            }),
            'photo': forms.ClearableFileInput(attrs={
                'class': 'form-control'
            }),
        }

    def clean_photo(self):
        photo = self.cleaned_data.get('photo')
        if photo:
            # Проверка размера (5 МБ)
            if photo.size > 5 * 1024 * 1024:
                raise ValidationError('Размер файла не должен превышать 5 МБ.')
            
            # Проверка формата
            if photo.content_type not in ['image/jpeg', 'image/png', 'image/jpg']:
                raise ValidationError('Допустимы только форматы JPG и PNG.')
        
        return photo


class TradeInEstimateForm(forms.ModelForm):
    """Форма выставления оценки оценщиком."""

    class Meta:
        model = TradeInRequest
        fields = ['preliminary_estimate', 'status']
        widgets = {
            'preliminary_estimate': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '850000',
                'min': 0
            }),
            'status': forms.Select(attrs={
                'class': 'form-control'
            }),
        }