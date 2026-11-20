from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from accounts.models import User
from catalog.models import CarModel, Trim, CarInStock, AdditionalEquipment
from testdrive.models import TestCar, TestDriveSlot
from booking.models import CarReservation
from tradein.models import TradeInRequest


class Command(BaseCommand):
    help = 'Заполняет базу демонстрационными данными'

    def handle(self, *args, **options):
        self.stdout.write('Начинаем заполнение базы...')

        # 1. Создаём пользователей всех ролей
        users_data = [
            ('admin_seed', 'admin', 'admin@test.ru'),
            ('manager_seed', 'manager', 'manager@test.ru'),
            ('appraiser_seed', 'appraiser', 'appraiser@test.ru'),
            ('customer_seed', 'customer', 'customer@test.ru'),
        ]

        for username, role, email in users_data:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={'role': role, 'email': email}
            )
            if created:
                user.set_password('12345')
                if role == 'customer':
                    user.driving_experience_years = 5
                    user.driver_license = '77 12 345678'
                user.save()
                self.stdout.write(f'  ✓ Создан пользователь: {username} ({role})')

        manager = User.objects.get(username='manager_seed')
        customer = User.objects.get(username='customer_seed')

        # 2. Создаём модели и комплектации
        data = [
            ('Haval', 'Jolion', 'SUV', [
                ('Comfort', '1.5T', 143, 'DCT', 'FWD', 2190000),
                ('Elite', '1.5T', 143, 'DCT', 'FWD', 2390000),
            ]),
            ('Chery', 'Tiggo 7 Pro', 'SUV', [
                ('Family', '1.5T', 147, 'CVT', 'FWD', 2490000),
            ]),
            ('Geely', 'Monjaro', 'SUV', [
                ('Luxury', '2.0T', 238, 'AT', 'AWD', 4190000),
            ]),
            ('Lada', 'Vesta', 'Седан', [
                ('Comfort', '1.6', 106, 'MT', 'FWD', 1290000),
            ]),
            ('Hyundai', 'Solaris', 'Седан', [
                ('Active', '1.4', 100, 'MT', 'FWD', 1390000),
            ]),
        ]

        trims_pool = []
        for brand, name, body, trims in data:
            model, _ = CarModel.objects.get_or_create(
                brand=brand, name=name, defaults={'body_type': body}
            )
            for tname, engine, hp, tr, dr, price in trims:
                trim, _ = Trim.objects.get_or_create(
                    car_model=model, name=tname,
                    defaults={
                        'engine': engine, 'power_hp': hp,
                        'transmission': tr, 'drivetrain': dr, 'price': price,
                    }
                )
                trims_pool.append(trim)

        self.stdout.write(f'  ✓ Создано комплектаций: {len(trims_pool)}')

        # 3. Создаём 30 машин на складе
        colors = ['Белый', 'Серый', 'Чёрный', 'Синий', 'Красный']
        for i in range(30):
            trim = trims_pool[i % len(trims_pool)]
            CarInStock.objects.get_or_create(
                vin=f'VIN{i:014d}',
                defaults={
                    'trim': trim,
                    'color': colors[i % len(colors)],
                    'status': 'available',
                    'arrival_date': timezone.now().date(),
                    'actual_price': trim.price,
                }
            )

        self.stdout.write('  ✓ Создано машин на складе: 30')

        # 4. Создаём доп. оборудование
        for name, price in [('Коврики', 5000), ('Сигнализация', 35000), ('Защита картера', 8000)]:
            AdditionalEquipment.objects.get_or_create(name=name, defaults={'price': price})

        # 5. Создаём тестовые авто
        test_cars = []
        for i, model in enumerate(CarModel.objects.all()[:3], start=1):
            test_car, _ = TestCar.objects.get_or_create(
                internal_number=f'TD-{i:03d}',
                defaults={
                    'model_ref': model,
                    'plate_number': f'А{100+i}ВС77',
                    'is_active': True,
                }
            )
            test_cars.append(test_car)

        self.stdout.write(f'  ✓ Создано тестовых авто: {len(test_cars)}')

        # 6. ПЕРЕСОЗДАЁМ СЛОТЫ (исправление ДЕФЕКТА 1)
        # Раньше было: timezone.now().replace(hour=hour) + timedelta(days=day)
        # Это создавало слот на СЕГОДНЯ в 10:00 + N дней — если сейчас 15:00, слот уже в прошлом
        # Теперь: (сегодня + N дней).replace(hour=hour) — всегда будущее
        deleted_count = TestDriveSlot.objects.all().delete()[0]
        self.stdout.write(f'  🗑️ Удалено старых слотов: {deleted_count}')

        hours = [10, 12, 14, 16]
        slots_created = 0

        for test_car in test_cars:
            for day_offset in range(1, 8):  # 7 дней вперёд
                for hour in hours:
                    future_date = timezone.now().date() + timedelta(days=day_offset)
                    start_time = timezone.make_aware(
                        timezone.datetime.combine(
                            future_date,
                            timezone.datetime.min.time().replace(hour=hour)
                        )
                    )

                    TestDriveSlot.objects.create(
                        test_car=test_car,
                        manager=manager,
                        start_time=start_time,
                        end_time=start_time + timedelta(hours=1),
                        is_blocked=False,
                    )
                    slots_created += 1

        self.stdout.write(f'  ✓ Создано новых слотов: {slots_created}')

        # 7. Создаём 1 заявку на трейд-ин (демо)
        TradeInRequest.objects.get_or_create(
            customer=customer,
            brand='Lada',
            model_name='Granta',
            defaults={
                'year': 2018,
                'mileage_km': 85000,
                'status': 'new',
            }
        )
        self.stdout.write('  ✓ Создана демо-заявка на трейд-ин')

        # ИТОГ
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 50))
        self.stdout.write(self.style.SUCCESS('✅ База данных успешно заполнена!'))
        self.stdout.write(self.style.SUCCESS('=' * 50))
        self.stdout.write('')
        self.stdout.write('Данные для входа:')
        self.stdout.write('  • admin_seed / 12345 — администратор')
        self.stdout.write('  • manager_seed / 12345 — менеджер')
        self.stdout.write('  • appraiser_seed / 12345 — оценщик')
        self.stdout.write('  • customer_seed / 12345 — покупатель')
        self.stdout.write('')
        self.stdout.write(f'Свободных слотов на тест-драйв: {TestDriveSlot.objects.filter(is_blocked=False).count()}')