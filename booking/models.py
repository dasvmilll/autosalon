from datetime import timedelta
from django.db import models
from django.utils import timezone
from accounts.models import User
from catalog.models import CarInStock, AdditionalEquipment


class CarReservation(models.Model):
    STATUS_CHOICES = [
        ('active', 'Активна'),
        ('expired', 'Снята автоматически'),
        ('converted', 'Переведена в договор'),
    ]
    car = models.ForeignKey(
        CarInStock, on_delete=models.PROTECT, related_name='reservations', verbose_name='Автомобиль'
    )
    customer = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='reservations', verbose_name='Покупатель'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    expires_at = models.DateTimeField(blank=True, verbose_name='Действует до')
    deposit_amount = models.DecimalField(
        max_digits=12, decimal_places=2, verbose_name='Сумма задатка'
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='active', verbose_name='Статус'
    )
    
    additional_equipment = models.ManyToManyField(
        AdditionalEquipment, blank=True, related_name='reservations',
        verbose_name='Дополнительное оборудование'
    )

    class Meta:
        verbose_name = 'Бронь автомобиля'
        verbose_name_plural = 'Брони автомобилей'
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.pk and not self.expires_at:
            self.expires_at = timezone.now() + timedelta(days=5)
        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        return self.status == 'active' and self.expires_at <= timezone.now()

    def __str__(self):
        return f'Бронь {self.car.vin} — {self.customer}'