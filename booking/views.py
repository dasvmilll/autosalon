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
    """Создание брони — длительная операция с транзакцией."""
    logger.info(f'reservation_create: пользователь {request.user.username} начал создание брони')
    
    if request.method == 'POST':
        form = CarReservationForm(request.POST)
        if form.is_valid():
            car = form.cleaned_data['car']
            
            if CarReservation.objects.filter(car=car, status='active').exists():
                logger.warning(f'reservation_create: попытка забронировать уже занятую машину VIN={car.vin}')
                messages.error(request, 'Этот автомобиль уже забронирован другим покупателем.')
                return redirect('booking:create')
            
            if car.status != 'available':
                logger.warning(f'reservation_create: машина VIN={car.vin} недоступна (статус={car.status})')
                messages.error(request, 'Этот автомобиль уже недоступен.')
                return redirect('catalog:list')
            
            try:
                with transaction.atomic():
                    reservation = form.save(commit=False)
                    reservation.customer = request.user
                    reservation.save()
                    car.status = 'reserved'
                    car.save(update_fields=['status'])
                
                logger.info(
                    f'reservation_create: УСПЕХ — создана бронь #{reservation.pk} '
                    f'пользователем {request.user.username} на VIN={car.vin}, '
                    f'задаток={reservation.deposit_amount}₽'
                )
                messages.success(request, 'Автомобиль забронирован на 5 дней.')
                return redirect('booking:my_list')
            
            except Exception as e:
                logger.error(
                    f'reservation_create: ОШИБКА при создании брони пользователем '
                    f'{request.user.username}: {type(e).__name__}: {str(e)}',
                    exc_info=True
                )
                messages.error(request, 'Произошла ошибка при бронировании. Попробуйте позже.')
                return redirect('booking:create')
        else:
            logger.warning(f'reservation_create: ошибки валидации формы: {form.errors}')
    else:
        form = CarReservationForm()
    return render(request, 'booking/create.html', {'form': form})


@login_required
def export_reservations_csv(request):
    logger.info(f'export_reservations_csv: пользователь {request.user.username} экспортировал брони в CSV')
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="reservations.csv"'
    response.write('\ufeff')
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