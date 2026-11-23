import logging
from django import forms
from django.core.exceptions import ValidationError
from .models import CarReservation
from catalog.models import CarInStock, AdditionalEquipment

logger = logging.getLogger(__name__)


class CarReservationForm(forms.ModelForm):
    """Форма бронирования автомобиля.
    
    ИСПРАВЛЕНИЕ УЯЗВИМОСТИ №5:
    - Добавлена проверка, что задаток — целое число (не дробное).
    - Добавлен атрибут step="1" в виджет NumberInput для запрета дробных чисел на уровне браузера.
    """
    
    # Поле дополнительного оборудования — чекбоксы
    equipment = forms.ModelMultipleChoiceField(
        queryset=AdditionalEquipment.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Дополнительное оборудование'
    )

    class Meta:
        model = CarReservation
        # ВАЖНО: 'car' должен быть здесь, иначе форма его проигнорирует
        fields = ['car', 'deposit_amount']
        widgets = {
            'car': forms.Select(attrs={'class': 'form-control'}),
            'deposit_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '50000',
                'min': 10000,
                'max': 500000,
                'step': 1,  # ИСПРАВЛЕНИЕ УЯЗВИМОСТИ №5: запрет дробных чисел на уровне браузера
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Показываем в форме только доступные машины
        self.fields['car'].queryset = CarInStock.objects.filter(status='available')
        # Если передали car_id через GET (с карточки авто), выбираем его по умолчанию
        car_id = kwargs.get('initial', {}).get('car')
        if car_id:
            self.fields['car'].queryset = CarInStock.objects.filter(pk=car_id, status='available')

    def clean_deposit_amount(self):
        """Валидация суммы задатка: от 10 000 до 500 000 ₽, только целые числа."""
        amount = self.cleaned_data.get('deposit_amount')
        
        if amount is None:
            raise ValidationError('Укажите сумму задатка.')
        
        # ИСПРАВЛЕНИЕ УЯЗВИМОСТИ №5: проверка, что задаток — целое число
        # Проверка для float
        if isinstance(amount, float) and not amount.is_integer():
            raise ValidationError('Сумма задатка должна быть целым числом.')
        
        # Проверка для Decimal (если поле в модели — DecimalField)
        if hasattr(amount, 'as_tuple'):
            if amount.as_tuple().exponent < 0:
                raise ValidationError('Сумма задатка должна быть целым числом.')
        
        if amount < 10000:
            raise ValidationError('Сумма задатка должна быть не менее 10 000 ₽.')
        if amount > 500000:
            raise ValidationError('Сумма задатка не может превышать 500 000 ₽.')
        
        return amount