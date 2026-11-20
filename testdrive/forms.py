import logging
from django import forms
from django.core.exceptions import ValidationError
from .models import TestDriveBooking
import re

logger = logging.getLogger(__name__)


class TestDriveBookingForm(forms.ModelForm):
    class Meta:
        model = TestDriveBooking
        fields = ['slot', 'license_number', 'experience_years']
        widgets = {
            'slot': forms.Select(attrs={'class': 'form-control'}),
            'license_number': forms.TextInput(attrs={
                'placeholder': '77 12 345678',
                'class': 'form-control',
            }),
            'experience_years': forms.NumberInput(attrs={
                'placeholder': '5',
                'class': 'form-control',
                'min': 0,
            }),
        }

    def clean_license_number(self):
        """Проверка номера ВУ по маске: 77 12 345678."""
        license_number = self.cleaned_data.get('license_number')
        if license_number:
            cleaned = license_number.strip()
            pattern = r'^\d{2}\s\d{2}\s\d{6}$'
            if not re.match(pattern, cleaned):
                logger.warning(f'clean_license_number: неверный формат "{license_number}"')
                raise ValidationError(
                    'Введите номер ВУ в формате: 77 12 345678 '
                    '(2 цифры, пробел, 2 цифры, пробел, 6 цифр).'
                )
        return license_number

    def clean_experience_years(self):
        """Стаж вождения должен быть не менее 2 лет."""
        years = self.cleaned_data.get('experience_years')
        # ИСПРАВЛЕНИЕ ДЕФЕКТА 3: проверяем на None ДО сравнения
        # Раньше было: if years < 2: → TypeError при None
        if years is None:
            logger.warning('clean_experience_years: поле стажа пустое')
            raise ValidationError('Укажите стаж вождения.')
        if years < 2:
            logger.warning(f'clean_experience_years: стаж {years} лет < 2')
            raise ValidationError('Стаж вождения должен быть не менее 2 лет.')
        return years