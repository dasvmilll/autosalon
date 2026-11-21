from django.core.exceptions import ValidationError, NON_FIELD_ERRORS
from django.db import models
from django.utils import timezone
from accounts.models import User
from catalog.models import CarModel


class TestCar(models.Model):
    model_ref = models.ForeignKey(CarModel, on_delete=models.PROTECT, related_name='test_cars', verbose_name='Модель')
    internal_number = models.CharField(max_length=20, unique=True, verbose_name='Внутренний номер')
    plate_number = models.CharField(max_length=15, verbose_name='Госномер')
    is_active = models.BooleanField(default=True, verbose_name='Активен')

    class Meta:
        verbose_name = 'Тестовый автомобиль'
        verbose_name_plural = 'Тестовые автомобили'

    def __str__(self):
        return f'{self.internal_number} — {self.model_ref}'


class TestDriveSlot(models.Model):
    test_car = models.ForeignKey(TestCar, on_delete=models.CASCADE, related_name='slots', verbose_name='Тестовый автомобиль')
    manager = models.ForeignKey(User, on_delete=models.PROTECT, limit_choices_to={'role': 'manager'}, related_name='managed_slots', verbose_name='Менеджер')
    start_time = models.DateTimeField(verbose_name='Время начала')
    end_time = models.DateTimeField(verbose_name='Время окончания')
    is_blocked = models.BooleanField(default=False, verbose_name='Заблокирован')

    class Meta:
        verbose_name = 'Слот тест-драйва'
        verbose_name_plural = 'Слоты тест-драйва'
        ordering = ['start_time']
        constraints = [
            models.CheckConstraint(condition=models.Q(end_time__gt=models.F('start_time')), name='slot_end_time_after_start_time')
        ]

    def __str__(self):
        return f'{self.test_car} | {self.start_time:%d.%m %H:%M}'


class TestDriveBooking(models.Model):
    STATUS_CHOICES = [
        ('created', 'Создана'),
        ('confirmed', 'Подтверждена'),
        ('completed', 'Завершена'),
        ('cancelled', 'Отменена'),
    ]
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='testdrive_bookings', verbose_name='Покупатель')
    slot = models.OneToOneField(TestDriveSlot, on_delete=models.PROTECT, related_name='booking', verbose_name='Слот')
    license_number = models.CharField(max_length=20, verbose_name='Номер ВУ')
    experience_years = models.PositiveIntegerField(verbose_name='Стаж вождения', null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='created', verbose_name='Статус')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    class Meta:
        verbose_name = 'Запись на тест-драйв'
        verbose_name_plural = 'Записи на тест-драйв'
        ordering = ['-created_at']

    def clean(self):
        errors = {}
        
        # 1. Проверка стажа (это поле есть в форме, поэтому оставляем 'experience_years')
        if self.experience_years is None or self.experience_years < 2:
            errors['experience_years'] = 'Стаж вождения должен быть не менее 2 лет.'
            
        # 2. Проверки, связанные со слотом (используем NON_FIELD_ERRORS, т.к. поля 'slot' нет в форме)
        if self.slot and self.slot.is_blocked:
            errors[NON_FIELD_ERRORS] = 'Выбранный слот закрыт для записи.'
            
        if self.slot and self.slot.pk:
            # Проверка занятости слота
            conflict = TestDriveBooking.objects.filter(slot=self.slot).exclude(status='cancelled').exclude(pk=self.pk)
            if conflict.exists():
                errors[NON_FIELD_ERRORS] = 'Этот слот уже занят.'
            
            # Проверка пересечений по авто и менеджеру
            overlaps = TestDriveSlot.objects.filter(
                models.Q(test_car=self.slot.test_car) | models.Q(manager=self.slot.manager),
                start_time__lt=self.slot.end_time,
                end_time__gt=self.slot.start_time
            ).exclude(pk=self.slot.pk)
            
            if overlaps.exists():
                errors[NON_FIELD_ERRORS] = 'Выбранное время пересекается с другим слотом (авто или менеджер заняты).'
                
        # 3. ИСПРАВЛЕНИЕ BUG-12: проверка, что покупатель не записан на другое авто в это же время
        if self.customer and self.slot and self.slot.pk:
            customer_conflict = TestDriveSlot.objects.filter(
                booking__customer=self.customer,
                booking__status__in=['created', 'confirmed'],
                start_time__lt=self.slot.end_time,
                end_time__gt=self.slot.start_time
            ).exclude(pk=self.slot.pk)
            
            if customer_conflict.exists():
                errors[NON_FIELD_ERRORS] = 'У вас уже есть запись на тест-драйв в это время.'
                
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.customer} — {self.slot}'