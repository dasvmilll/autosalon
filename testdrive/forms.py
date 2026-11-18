from django import forms
from django.core.exceptions import ValidationError
from .models import TestDriveBooking

class TestDriveBookingForm(forms.ModelForm):
    class Meta:
        model = TestDriveBooking
        fields = ['slot', 'license_number', 'experience_years']
        widgets = {
            'slot': forms.Select(attrs={'class': 'form-control'}),
            'license_number': forms.TextInput(attrs={'placeholder': '77 12 345678', 'class': 'form-control'}),
            'experience_years': forms.NumberInput(attrs={'placeholder': '5', 'class': 'form-control'}),
        }

    def clean_experience_years(self):
        years = self.cleaned_data.get('experience_years')
        if years < 2:
            raise ValidationError('Стаж вождения должен быть не менее 2 лет.')
        return years