from django.core.exceptions import ValidationError
from django.db import models
from accounts.models import User
from catalog.models import CarModel


class TestCar(models.Model):
    model_ref = models.ForeignKey(
        CarModel, on_delete=models.PROTECT, related_name='test_cars', verbose_name='Модель'
    )
    internal_number = models.CharField(max_length=20, unique=True, verbose_name='Внутренний номер')
    plate_number = models.CharField(max_length=15, verbose_name='Госномер')
    is_active = models.BooleanField(default=True, verbose_name='Активен')

    class Meta:
        verbose_name = 'Тестовый автомобиль'
        verbose_name_plural = 'Тестовые автомобили'

    def __str__(self):
        return f'{self.internal_number} — {self.model_ref}'


class TestDriveSlot(models.Model):
    test_car = models.ForeignKey(
        TestCar, on_delete=models.CASCADE, related_name='slots', verbose_name='Тестовый автомобиль'
    )
    manager = models.ForeignKey(
        User, on_delete=models.PROTECT, limit_choices_to={'role': 'manager'},
        related_name='managed_slots', verbose_name='Менеджер'
    )
    start_time = models.DateTimeField(verbose_name='Время начала')
    end_time = models.DateTimeField(verbose_name='Время окончания')
    is_blocked = models.BooleanField(default=False, verbose_name='Заблокирован')

    class Meta:
        verbose_name = 'Слот тест-драйва'
        verbose_name_plural = 'Слоты тест-драйва'
        ordering = ['start_time']
        constraints = [
            models.CheckConstraint(
                condition=models.Q(end_time__gt=models.F('start_time')),
                name='slot_end_time_after_start_time'
            )
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
    customer = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='testdrive_bookings', verbose_name='Покупатель'
    )
    slot = models.OneToOneField(
        TestDriveSlot, on_delete=models.PROTECT, related_name='booking', verbose_name='Слот'
    )
    license_number = models.CharField(max_length=20, verbose_name='Номер ВУ')
    experience_years = models.PositiveIntegerField(verbose_name='Стаж вождения')
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='created', verbose_name='Статус'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    class Meta:
        verbose_name = 'Запись на тест-драйв'
        verbose_name_plural = 'Записи на тест-драйв'
        ordering = ['-created_at']

    def clean(self):
        errors = {}
        if self.experience_years < 2:
            errors['experience_years'] = 'Стаж вождения должен быть не менее 2 лет.'
        if self.slot and self.slot.is_blocked:
            errors['slot'] = 'Выбранный слот закрыт для записи.'
        if self.slot and self.slot.pk:
            conflict = TestDriveBooking.objects.filter(
                slot=self.slot
            ).exclude(status='cancelled').exclude(pk=self.pk)
            if conflict.exists():
                errors['slot'] = 'Этот слот уже занят.'
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.customer} — {self.slot}'