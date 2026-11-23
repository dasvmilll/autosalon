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
        """Серверная валидация загружаемого файла."""
        photo = self.cleaned_data.get('photo')

        # ИСПРАВЛЕНИЕ УЯЗВИМОСТИ №2: фото обязательно
        if not photo:
            raise ValidationError('Пожалуйста, загрузите фотографию автомобиля.')

        # ИСПРАВЛЕНИЕ УЯЗВИМОСТИ №1 (BUG-16): проверка размера (5 МБ)
        MAX_SIZE = 5 * 1024 * 1024
        if photo.size > MAX_SIZE:
            raise ValidationError(
                f'Размер файла не должен превышать 5 МБ. '
                f'Ваш файл: {photo.size / (1024 * 1024):.2f} МБ.'
            )

        # ИСПРАВЛЕНИЕ УЯЗВИМОСТИ №1: проверка расширения
        allowed_extensions = ['jpg', 'jpeg', 'png']
        ext = photo.name.rsplit('.', 1)[-1].lower() if '.' in photo.name else ''
        if ext not in allowed_extensions:
            raise ValidationError(
                f'Разрешены только файлы форматов JPG и PNG. '
                f'Вы загрузили файл с расширением: .{ext}'
            )

        # ИСПРАВЛЕНИЕ УЯЗВИМОСТИ №1: проверка MIME-типа (защита от file.php.jpg)
        content_type = getattr(photo, 'content_type', '')
        if content_type and content_type not in ['image/jpeg', 'image/png']:
            raise ValidationError(
                'Файл не является корректным изображением (проверьте MIME-тип).'
            )

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