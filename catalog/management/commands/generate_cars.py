"""
Команда для генерации большого количества автомобилей (для проверки на объёме).
Запуск: python manage.py generate_cars 1000
"""
import random
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from catalog.models import CarModel, Trim, CarInStock


class Command(BaseCommand):
    help = 'Генерирует N автомобилей в базе для проверки на объёме'

    def add_arguments(self, parser):
        parser.add_argument('count', type=int, help='Количество машин для генерации')

    def handle(self, *args, **options):
        count = options['count']
        self.stdout.write(f'Генерируем {count} автомобилей...')

        # Проверяем, что есть хотя бы одна комплектация
        trims = list(Trim.objects.all())
        if not trims:
            self.stdout.write(self.style.ERROR('Сначала запустите seed_data!'))
            return

        colors = ['Белый', 'Серый', 'Чёрный', 'Синий', 'Красный', 'Зелёный', 'Серебристый']
        
        # Узнаём, сколько машин уже есть, чтобы не дублировать VIN
        existing_count = CarInStock.objects.count()
        
        created = 0
        for i in range(count):
            trim = random.choice(trims)
            vin = f'GEN{existing_count + i:014d}'
            
            # Небольшая вариация цены (±10% от базовой)
            # ИСПРАВЛЕНИЕ: конвертируем Decimal в float перед умножением
            price_variation = random.uniform(0.9, 1.1)
            actual_price = int(float(trim.price) * price_variation)
            
            # Случайная дата прибытия (последние 30 дней)
            arrival_date = timezone.now().date() - timedelta(days=random.randint(0, 30))
            
            CarInStock.objects.create(
                vin=vin,
                trim=trim,
                color=random.choice(colors),
                status='available',
                arrival_date=arrival_date,
                actual_price=actual_price,
            )
            created += 1

        self.stdout.write(self.style.SUCCESS(f'✅ Создано {created} автомобилей'))
        self.stdout.write(f'Всего машин в базе: {CarInStock.objects.count()}')