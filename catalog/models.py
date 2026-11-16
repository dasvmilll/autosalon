from django.db import models


class CarModel(models.Model):
    brand = models.CharField(max_length=50, verbose_name='Марка')
    name = models.CharField(max_length=100, verbose_name='Модель')
    body_type = models.CharField(max_length=30, verbose_name='Тип кузова')
    description = models.TextField(blank=True, verbose_name='Описание')

    class Meta:
        verbose_name = 'Модель автомобиля'
        verbose_name_plural = 'Модели автомобилей'
        ordering = ['brand', 'name']

    def __str__(self):
        return f'{self.brand} {self.name}'


class Trim(models.Model):
    car_model = models.ForeignKey(
        CarModel, on_delete=models.CASCADE, related_name='trims', verbose_name='Модель'
    )
    name = models.CharField(max_length=100, verbose_name='Название комплектации')
    engine = models.CharField(max_length=50, verbose_name='Двигатель')
    power_hp = models.PositiveIntegerField(verbose_name='Мощность (л.с.)')
    transmission = models.CharField(max_length=30, verbose_name='КПП')
    drivetrain = models.CharField(max_length=30, verbose_name='Привод')
    price = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Цена')

    class Meta:
        verbose_name = 'Комплектация'
        verbose_name_plural = 'Комплектации'
        ordering = ['car_model', 'name']

    def __str__(self):
        return f'{self.car_model} — {self.name}'


class CarInStock(models.Model):
    STATUS_CHOICES = [
        ('available', 'Свободен'),
        ('reserved', 'Забронирован'),
        ('sold', 'Продан'),
    ]
    vin = models.CharField(max_length=17, unique=True, verbose_name='VIN')
    trim = models.ForeignKey(
        Trim, on_delete=models.PROTECT, related_name='stock_cars', verbose_name='Комплектация'
    )
    color = models.CharField(max_length=50, verbose_name='Цвет')
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='available', verbose_name='Статус'
    )
    arrival_date = models.DateField(null=True, blank=True, verbose_name='Дата поступления')
    actual_price = models.DecimalField(
        max_digits=12, decimal_places=2, verbose_name='Фактическая цена'
    )

    class Meta:
        verbose_name = 'Автомобиль на складе'
        verbose_name_plural = 'Автомобили на складе'
        ordering = ['-arrival_date']

    def __str__(self):
        return f'{self.vin} — {self.trim}'


class AdditionalEquipment(models.Model):
    name = models.CharField(max_length=100, verbose_name='Название')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена')
    compatible_trims = models.ManyToManyField(
        Trim, blank=True, related_name='compatible_equipment', verbose_name='Совместимые комплектации'
    )

    class Meta:
        verbose_name = 'Дополнительное оборудование'
        verbose_name_plural = 'Дополнительное оборудование'

    def __str__(self):
        return self.name