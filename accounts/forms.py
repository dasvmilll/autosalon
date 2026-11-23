from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from .models import User


# ============================================
# ИСПРАВЛЕНИЕ УЯЗВИМОСТИ №6: Валидатор формата телефона
# Принимает только российские номера в формате +7XXXXXXXXXX
# ============================================
phone_validator = RegexValidator(
    regex=r'^\+7\d{10}$',
    message='Введите номер телефона в формате: +79991234567 (12 символов, начиная с +7)'
)


class CustomUserCreationForm(UserCreationForm):
    """Кастомная форма регистрации с CSS-классами для стилизации.
    
    ИСПРАВЛЕНИЕ УЯЗВИМОСТИ №6: добавлена валидация формата телефона.
    ИСПРАВЛЕНИЕ УЯЗВИМОСТИ №7: добавлена проверка длины имени пользователя (макс. 150 символов).
    """
    
    class Meta:
        model = User
        fields = ['username', 'email', 'phone', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Имя пользователя',
                'maxlength': 150,  # ИСПРАВЛЕНИЕ УЯЗВИМОСТИ №7
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'email@example.com',
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+79001234567',
                'pattern': r'\+7\d{10}',  # ИСПРАВЛЕНИЕ УЯЗВИМОСТИ №6: клиентская валидация
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Добавляем CSS-классы к полям паролей
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Пароль',
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Подтверждение пароля',
        })
        # Меняем метки на русский
        self.fields['username'].label = 'Имя пользователя'
        self.fields['email'].label = 'Email'
        self.fields['phone'].label = 'Телефон'
        self.fields['password1'].label = 'Пароль'
        self.fields['password2'].label = 'Подтверждение пароля'

    # ИСПРАВЛЕНИЕ УЯЗВИМОСТИ №6: серверная валидация телефона
    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
        if phone:
            phone_validator(phone)  # Вызовет ValidationError, если формат неверный
        return phone

    # ИСПРАВЛЕНИЕ УЯЗВИМОСТИ №7: проверка длины имени
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username and len(username) > 150:
            raise ValidationError('Имя пользователя не может быть длиннее 150 символов.')
        return username


class ProfileForm(forms.ModelForm):
    """Форма для редактирования профиля пользователя.
    
    ИСПРАВЛЕНИЕ УЯЗВИМОСТИ №6: добавлена валидация формата телефона.
    """
    
    class Meta:
        model = User
        fields = ['phone', 'driver_license', 'driving_experience_years']
        widgets = {
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+79001234567',
                'pattern': r'\+7\d{10}',  # ИСПРАВЛЕНИЕ УЯЗВИМОСТИ №6: клиентская валидация
            }),
            'driver_license': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '77 12 345678',
            }),
            'driving_experience_years': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '5',
                'min': 0,
            }),
        }
        labels = {
            'phone': 'Телефон',
            'driver_license': 'Номер водительского удостоверения',
            'driving_experience_years': 'Стаж вождения (лет)',
        }

    # ИСПРАВЛЕНИЕ УЯЗВИМОСТИ №6: серверная валидация телефона
    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
        if phone:
            phone_validator(phone)  # Вызовет ValidationError, если формат неверный
        return phone