import csv
import logging
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from catalog.models import CarInStock
from .forms import CarReservationForm
from .models import CarReservation

logger = logging.getLogger(__name__)


@login_required
def my_reservations(request):
    """Список моих броней."""
    reservations = CarReservation.objects.filter(customer=request.user).select_related('car__trim__car_model')
    return render(request, 'booking/my_list.html', {'reservations': reservations})


@login_required
def reservation_detail(request, pk):
    """Просмотр конкретной брони (FR-18)."""
    reservation = get_object_or_404(CarReservation, pk=pk, customer=request.user)
    logger.info(f'reservation_detail: пользователь {request.user.username} открыл бронь #{pk}')
    return render(request, 'booking/detail.html', {'reservation': reservation})


@login_required
def reservation_create(request):
    """Создание брони автомобиля."""
    
    # Если пришли с карточки авто, берем его ID из URL
    car_id = request.GET.get('car')
    initial_data = {'car': car_id} if car_id else {}

    if request.method == 'POST':
        form = CarReservationForm(request.POST)
        if form.is_valid():
            # Создаем объект в памяти, но не сохраняем в БД сразу
            reservation = form.save(commit=False)
            
            # Привязываем текущего пользователя
            reservation.customer = request.user
            
            # ЯВНАЯ ПРОВЕРКА: если автомобиль не привязался из формы, берем его из GET
            if not reservation.car and car_id:
                try:
                    reservation.car = CarInStock.objects.get(pk=car_id, status='available')
                except CarInStock.DoesNotExist:
                    messages.error(request, 'Выбранный автомобиль недоступен для бронирования.')
                    return render(request, 'booking/create.html', {'form': form})
            
            if not reservation.car:
                messages.error(request, 'Необходимо выбрать автомобиль.')
                return render(request, 'booking/create.html', {'form': form})

            # Дополнительная проверка: не забронирована ли уже эта машина
            if CarReservation.objects.filter(car=reservation.car, status='active').exists():
                messages.error(request, 'Этот автомобиль уже забронирован другим покупателем.')
                return render(request, 'booking/create.html', {'form': form})

            try:
                with transaction.atomic():
                    # 1. Сохраняем саму бронь (теперь car точно не None)
                    reservation.save()
                    
                    # 2. Сохраняем связь ManyToMany (дополнительное оборудование)
                    equipment = form.cleaned_data.get('equipment')
                    if equipment:
                        reservation.equipment.set(equipment)
                    
                    # 3. Меняем статус автомобиля на "зарезервирован"
                    reservation.car.status = 'reserved'
                    reservation.car.save(update_fields=['status'])
                
                logger.info(f'УСПЕХ: создана бронь #{reservation.pk} пользователем {request.user.username} на авто {reservation.car.vin}')
                messages.success(request, 'Автомобиль успешно забронирован на 5 дней!')
                return redirect('booking:my_list')
            
            except Exception as e:
                logger.error(f'ОШИБКА при создании брони: {type(e).__name__}: {str(e)}', exc_info=True)
                messages.error(request, 'Произошла техническая ошибка при бронировании. Попробуйте позже.')
        else:
            logger.warning(f'Ошибки валидации формы бронирования: {form.errors}')
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')
    else:
        form = CarReservationForm(initial=initial_data)

    return render(request, 'booking/create.html', {'form': form})


@login_required
def export_reservations_csv(request):
    """Экспорт броней в CSV."""
    logger.info(f'export_reservations_csv: пользователь {request.user.username} экспортировал брони в CSV')
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="reservations.csv"'
    response.write('\ufeff') # BOM для корректного открытия в Excel
    writer = csv.writer(response, delimiter=';')
    writer.writerow(['VIN', 'Покупатель', 'Дата создания', 'Действует до', 'Задаток', 'Статус'])
    qs = CarReservation.objects.filter(customer=request.user).select_related('customer', 'car')
    for r in qs:
        writer.writerow([
            r.car.vin, r.customer.username,
            r.created_at.strftime('%d.%m.%Y %H:%M'),
            r.expires_at.strftime('%d.%m.%Y %H:%M'),
            r.deposit_amount, r.get_status_display(),
        ])
    return response