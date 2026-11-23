from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from accounts.models import User
from catalog.models import CarModel, Trim, CarInStock, AdditionalEquipment
from testdrive.models import TestCar, TestDriveSlot, TestDriveBooking
from booking.models import CarReservation
from tradein.models import TradeInRequest


class Command(BaseCommand):
    help = 'Заполняет базу демонстрационными данными для тестирования'

    def handle(self, *args, **options):
        self.stdout.write('Начинаем заполнение базы...')

        # 1. Создаём пользователей всех ролей
        users_data = [
            ('admin_seed', 'admin', 'admin@test.ru'),
            ('manager_seed1', 'manager', 'manager1@test.ru'),
            ('manager_seed2', 'manager', 'manager2@test.ru'),
            ('manager_seed3', 'manager', 'manager3@test.ru'),
            ('appraiser_seed', 'appraiser', 'appraiser@test.ru'),
            ('customer_seed', 'customer', 'customer@test.ru'),
            ('customer_seed2', 'customer', 'customer2@test.ru'),  # для проверки чужих записей
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

        managers = [
            User.objects.get(username='manager_seed1'),
            User.objects.get(username='manager_seed2'),
            User.objects.get(username='manager_seed3'),
        ]
        customer = User.objects.get(username='customer_seed')
        customer2 = User.objects.get(username='customer_seed2')

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

        # 5. Создаём тестовые авто (3 шт)
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
            test_cars.append((test_car, managers[i - 1]))  # (авто, менеджер)
            self.stdout.write(f'  ✓ Создано тестовое авто: {test_car.internal_number} (менеджер: {managers[i-1].username})')

        # 6. ПЕРЕСОЗДАЁМ СЛОТЫ (исправление всех прошлых ошибок)
        # ИСПРАВЛЕНИЕ: сначала удаляем записи, потом слоты (из-за on_delete=PROTECT)
        deleted_bookings = TestDriveBooking.objects.all().delete()[0]
        self.stdout.write(f'  🗑️ Удалено старых записей на тест-драйв: {deleted_bookings}')
        
        deleted_count = TestDriveSlot.objects.all().delete()[0]
        self.stdout.write(f'  🗑️ Удалено старых слотов: {deleted_count}')

        # ИСПРАВЛЕНИЕ: создаём слоты ТОЛЬКО на будущее
        hours = [10, 12, 14, 16]
        slots_created = 0
        all_slots = []  # сохраняем для создания тестовых записей

        for test_car, manager in test_cars:
            for day_offset in range(1, 8):  # 7 дней вперёд
                for hour in hours:
                    future_date = timezone.now().date() + timedelta(days=day_offset)
                    start_time = timezone.make_aware(
                        timezone.datetime.combine(
                            future_date,
                            timezone.datetime.min.time().replace(hour=hour)
                        )
                    )

                    slot = TestDriveSlot.objects.create(
                        test_car=test_car,
                        manager=manager,
                        start_time=start_time,
                        end_time=start_time + timedelta(hours=1),
                        is_blocked=False,
                    )
                    all_slots.append(slot)
                    slots_created += 1

        self.stdout.write(f'  ✓ Создано новых слотов: {slots_created}')

        # 7. Создаём тестовые записи на тест-драйв (для тест-кейсов)
        # Удаляем старые записи
        TestDriveBooking.objects.all().delete()

        # TC-07/TC-09: активная запись customer_seed (для проверки отмены)
        if len(all_slots) >= 1:
            TestDriveBooking.objects.create(
                customer=customer,
                slot=all_slots[0],
                license_number='77 12 345678',
                experience_years=5,
                status='created',
            )
            self.stdout.write('  ✓ Создана запись на тест-драйв: статус "Создана" (для TC-07, TC-09)')

        # TC-10: завершённая запись (для проверки, что её нельзя отменить)
        if len(all_slots) >= 2:
            TestDriveBooking.objects.create(
                customer=customer,
                slot=all_slots[1],
                license_number='77 12 345678',
                experience_years=5,
                status='completed',
            )
            self.stdout.write('  ✓ Создана запись на тест-драйв: статус "Завершена" (для TC-10)')

        # Запись другого пользователя (для проверки FR-18 — чужие записи)
        if len(all_slots) >= 3:
            TestDriveBooking.objects.create(
                customer=customer2,
                slot=all_slots[2],
                license_number='77 99 888888',
                experience_years=3,
                status='created',
            )
            self.stdout.write('  ✓ Создана запись другого пользователя (для FR-18)')

        # 8. Создаём тестовые брони (для тест-кейсов)
        CarReservation.objects.all().delete()
        # Возвращаем все машины в статус available
        CarInStock.objects.update(status='available')

        # Активная бронь customer_seed (для TC-11)
        car1 = CarInStock.objects.filter(status='available').first()
        if car1:
            CarReservation.objects.create(
                car=car1,
                customer=customer,
                deposit_amount=50000,
                status='active',
            )
            car1.status = 'reserved'
            car1.save(update_fields=['status'])
            self.stdout.write(f'  ✓ Создана активная бронь на VIN={car1.vin} (для TC-11)')

        # 9. Создаём тестовые заявки на трейд-ин
        TradeInRequest.objects.all().delete()

        # Новая заявка (для TC-13)
        TradeInRequest.objects.create(
            customer=customer,
            brand='Toyota',
            model_name='Camry',
            year=2019,
            mileage_km=45000,
            status='new',
        )
        self.stdout.write('  ✓ Создана новая заявка на трейд-ин (для TC-13)')

        # Оценённая заявка
        TradeInRequest.objects.create(
            customer=customer,
            brand='Kia',
            model_name='Rio',
            year=2020,
            mileage_km=30000,
            status='estimated',
            appraiser=User.objects.get(username='appraiser_seed'),
            preliminary_estimate=850000,
        )
        self.stdout.write('  ✓ Создана оценённая заявка на трейд-ин')

        # ИТОГ
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('✅ База данных успешно заполнена для тестирования!'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write('')
        self.stdout.write('📋 Учётные записи:')
        self.stdout.write('  • admin_seed / 12345       — администратор')
        self.stdout.write('  • manager_seed1 / 12345    — менеджер TD-001')
        self.stdout.write('  • manager_seed2 / 12345    — менеджер TD-002')
        self.stdout.write('  • manager_seed3 / 12345    — менеджер TD-003')
        self.stdout.write('  • appraiser_seed / 12345   — оценщик')
        self.stdout.write('  • customer_seed / 12345    — покупатель (стаж 5 лет, ВУ: 77 12 345678)')
        self.stdout.write('  • customer_seed2 / 12345   — второй покупатель (для FR-18)')
        self.stdout.write('')
        self.stdout.write('📊 Статистика:')
        self.stdout.write(f'  • Машин на складе: {CarInStock.objects.count()}')
        self.stdout.write(f'  • Свободных машин: {CarInStock.objects.filter(status="available").count()}')
        self.stdout.write(f'  • Слотов тест-драйва: {TestDriveSlot.objects.filter(is_blocked=False).count()}')
        self.stdout.write(f'  • Записей на тест-драйв: {TestDriveBooking.objects.count()}')
        self.stdout.write(f'  • Броней: {CarReservation.objects.count()}')
        self.stdout.write(f'  • Заявок на трейд-ин: {TradeInRequest.objects.count()}')