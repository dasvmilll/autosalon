import logging
from django.db.models import Count, Sum, Avg
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect
from catalog.models import CarInStock
from accounts.forms import ProfileForm

logger = logging.getLogger(__name__)


def home(request):
    logger.info('home: загрузка главной страницы')
    # ИСПРАВЛЕНИЕ N+1: добавлен select_related('trim__car_model')
    cars = CarInStock.objects.filter(status='available').select_related('trim__car_model')[:3]
    return render(request, 'core/home.html', {'cars': cars})


def dashboard(request):
    logger.info('dashboard: загрузка страницы статистики')
    cars = CarInStock.objects.all()
    total = cars.count()
    total_price = cars.aggregate(Sum('actual_price'))['actual_price__sum'] or 0
    # ИСПРАВЛЕНИЕ ДЕФЕКТА 2: добавлено 'or 0' для защиты от None
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
    logger.info(f'profile: пользователь {request.user.username} открыл профиль')
    return render(request, 'profile.html')


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