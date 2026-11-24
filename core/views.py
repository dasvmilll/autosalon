import logging
from django.db.models import Count, Sum, Avg
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect
from catalog.models import CarInStock
from accounts.forms import ProfileForm
from booking.models import CarReservation
from testdrive.models import TestDriveBooking
from tradein.models import TradeInRequest

logger = logging.getLogger(__name__)


def home(request):
    logger.info('home: загрузка главной страницы')
    cars = CarInStock.objects.filter(status='available').select_related('trim__car_model')[:3]
    return render(request, 'core/home.html', {'cars': cars})


def dashboard(request):
    logger.info('dashboard: загрузка страницы статистики')
    cars = CarInStock.objects.all()
    total = cars.count()
    total_price = cars.aggregate(Sum('actual_price'))['actual_price__sum'] or 0
    avg_price = cars.aggregate(Avg('actual_price'))['actual_price__avg'] or 0
    reserved = cars.filter(status='reserved').count()
    reserved_percent = round(reserved / total * 100, 1) if total > 0 else 0
    status_data = [
        cars.filter(status='available').count(),
        cars.filter(status='reserved').count(),
        cars.filter(status='sold').count(),
    ]
    logger.info(f'dashboard: всего машин={total}, средняя цена={avg_price}')
    return render(request, 'core/dashboard.html', {
        'total': total,
        'total_price': total_price,
        'avg_price': avg_price,
        'reserved_percent': reserved_percent,
        'status_data': status_data,
    })


@login_required
def profile(request):
    """Личный кабинет пользователя со статистикой и последними записями."""
    user = request.user
    logger.info(f'profile: пользователь {user.username} открыл профиль')
    
    stats = {}
    recent = {}
    
    if user.role == 'customer':
        # Статистика
        stats['reservations_count'] = CarReservation.objects.filter(customer=user).count()
        stats['active_reservations'] = CarReservation.objects.filter(
            customer=user, status='active'
        ).count()
        stats['bookings_count'] = TestDriveBooking.objects.filter(customer=user).count()
        stats['active_bookings'] = TestDriveBooking.objects.filter(
            customer=user, status='created'
        ).count()
        stats['tradeins_count'] = TradeInRequest.objects.filter(customer=user).count()
        stats['new_tradeins'] = TradeInRequest.objects.filter(
            customer=user, status='new'
        ).count()
        
        # Последние записи (для отображения в профиле)
        recent['bookings'] = TestDriveBooking.objects.filter(
            customer=user
        ).select_related('slot__test_car').order_by('-created_at')[:3]
        
        recent['reservations'] = CarReservation.objects.filter(
            customer=user
        ).select_related('car__trim__car_model').order_by('-created_at')[:3]
        
        recent['tradeins'] = TradeInRequest.objects.filter(
            customer=user
        ).order_by('-created_at')[:3]
        
    elif user.role == 'manager':
        stats['managed_slots'] = user.managed_slots.count()
        stats['bookings'] = TestDriveBooking.objects.filter(slot__manager=user).count()
        
    elif user.role == 'appraiser':
        stats['tradeins'] = TradeInRequest.objects.filter(appraiser=user).count()
    
    return render(request, 'profile.html', {
        'stats': stats,
        'recent': recent,
    })


@login_required
def profile_edit(request):
    """Редактирование профиля пользователя."""
    logger.info(f'profile_edit: пользователь {request.user.username} открыл форму')
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            logger.info(f'profile_edit: профиль {request.user.username} успешно обновлён')
            messages.success(request, 'Профиль успешно обновлён.')
            return redirect('core:profile')
        else:
            logger.warning(f'profile_edit: ошибки валидации формы: {form.errors}')
    else:
        form = ProfileForm(instance=request.user)
    return render(request, 'profile_edit.html', {'form': form})

# ЗАДАНИЕ 16: Кастомные обработчики ошибок
def custom_400(request, exception):
    """400 — некорректный запрос."""
    return render(request, '400.html', status=400)


def custom_403(request, exception):
    """403 — доступ запрещён."""
    return render(request, '403.html', status=403)


def custom_404(request, exception):
    """404 — страница не найдена."""
    return render(request, '404.html', status=404)


def custom_500(request):
    """500 — внутренняя ошибка сервера."""
    return render(request, '500.html', status=500)