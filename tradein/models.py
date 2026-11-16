from django.db import models
from accounts.models import User


class TradeInRequest(models.Model):
    STATUS_CHOICES = [
        ('new', 'Новая'),
        ('estimated', 'Оценена'),
        ('accepted', 'Принята'),
        ('rejected', 'Отклонена'),
    ]
    customer = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='tradein_requests', verbose_name='Покупатель'
    )
    brand = models.CharField(max_length=50, verbose_name='Марка')
    model_name = models.CharField(max_length=100, verbose_name='Модель')
    year = models.PositiveIntegerField(verbose_name='Год выпуска')
    mileage_km = models.PositiveIntegerField(verbose_name='Пробег (км)')
    photo = models.ImageField(
        upload_to='tradein/', blank=True, null=True, verbose_name='Фото автомобиля'
    )
    preliminary_estimate = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
        verbose_name='Предварительная оценка'
    )
    appraiser = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        limit_choices_to={'role': 'appraiser'}, related_name='assigned_tradeins',
        verbose_name='Оценщик'
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='new', verbose_name='Статус'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    class Meta:
        verbose_name = 'Заявка на трейд-ин'
        verbose_name_plural = 'Заявки на трейд-ин'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.brand} {self.model_name} ({self.year})'