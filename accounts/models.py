from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = [
        ('customer', 'Покупатель'),
        ('manager', 'Менеджер отдела продаж'),
        ('appraiser', 'Оценщик трейд-ин'),
        ('admin', 'Администратор автосалона'),
    ]
    role = models.CharField(
        max_length=20, choices=ROLE_CHOICES, default='customer', verbose_name='Роль'
    )
    phone = models.CharField(max_length=20, blank=True, verbose_name='Телефон')
    driver_license = models.CharField(max_length=20, blank=True, verbose_name='Номер ВУ')
    driving_experience_years = models.PositiveIntegerField(
        default=0, verbose_name='Стаж вождения (лет)'
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return f'{self.username} ({self.get_role_display()})'