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

        # 1. Создаем пользователей
        manager, created = User.objects.get_or_create(
            username='manager_seed',
            defaults={'role': 'manager', 'email': 'manager@test.ru'}
        )
        if created:
            manager.set_password('12345')
            manager.save()
            
        customer, created = User.objects.get_or_create(
            username='customer_seed',
            defaults={'role': 'customer', 'email': 'customer@test.ru', 'driving_experience_years': 5}
        )
        if created:
            customer.set_password('12345')
            customer.save()

        # 2. Создаем модели и комплектации
        data = [
            ('Haval', 'Jolion', 'SUV', [('Comfort', '1.5T', 143, 'DCT', 'FWD', 2190000),
                                         ('Elite', '1.5T', 143, 'DCT', 'FWD', 2390000)]),
            ('Chery', 'Tiggo 7 Pro', 'SUV', [('Family', '1.5T', 147, 'CVT', 'FWD', 2490000)]),
            ('Geely', 'Monjaro', 'SUV', [('Luxury', '2.0T', 238, 'AT', 'AWD', 4190000)]),
            ('Lada', 'Vesta', 'Седан', [('Comfort', '1.6', 106, 'MT', 'FWD', 1290000)]),
            ('Hyundai', 'Solaris', 'Седан', [('Active', '1.4', 100, 'MT', 'FWD', 1390000)]),
        ]

        trims_pool = []
        for brand, name, body, trims in data:
            model, _ = CarModel.objects.get_or_create(
                brand=brand, name=name, defaults={'body_type': body}
            )
            for tname, engine, hp, tr, dr, price in trims:
                trim, _ = Trim.objects.get_or_create(
                    car_model=model, name=tname,
                    defaults={'engine': engine, 'power_hp': hp,
                              'transmission': tr, 'drivetrain': dr, 'price': price}
                )
                trims_pool.append(trim)

        # 3. Создаем 30 машин на складе
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

        # 4. Создаем доп. оборудование
        for name, price in [('Коврики', 5000), ('Сигнализация', 35000), ('Защита картера', 8000)]:
            AdditionalEquipment.objects.get_or_create(name=name, defaults={'price': price})

        # 5. Создаем тестовые авто и слоты (10+)
        for i, model in enumerate(CarModel.objects.all()[:3], start=1):
            test_car, _ = TestCar.objects.get_or_create(
                internal_number=f'TD-{i:03d}',
                defaults={'model_ref': model, 'plate_number': f'А{100+i}ВС77'}
            )
            for day in range(1, 6):
                for hour in [10, 12, 14]:
                    start = timezone.now().replace(hour=hour, minute=0, second=0, microsecond=0) + timedelta(days=day)
                    TestDriveSlot.objects.get_or_create(
                        test_car=test_car, manager=manager, start_time=start,
                        defaults={'end_time': start + timedelta(hours=1)}
                    )

        # 6. Создаем 1 бронь и 1 заявку на трейд-ин (чтобы в базе были все сущности)
        car_to_reserve = CarInStock.objects.first()
        if car_to_reserve:
            CarReservation.objects.get_or_create(
                car=car_to_reserve, customer=customer,
                defaults={'deposit_amount': 50000, 'status': 'active'}
            )

        TradeInRequest.objects.get_or_create(
            customer=customer, brand='Lada', model_name='Granta',
            defaults={'year': 2018, 'mileage_km': 85000, 'status': 'new'}
        )

        self.stdout.write(self.style.SUCCESS('База данных успешно заполнена!'))