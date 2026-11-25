import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.utils import timezone
from django.views.decorators.http import require_POST
from .models import TestDriveSlot, TestDriveBooking
from .forms import TestDriveBookingForm

logger = logging.getLogger(__name__)


def slot_list(request):
    """Список свободных слотов."""
    try:
        slots = TestDriveSlot.objects.filter(
            is_blocked=False,
            start_time__gte=timezone.now()
        ).exclude(
            booking__status__in=['created', 'confirmed']
        ).order_by('start_time').select_related('test_car', 'manager')
        
        logger.info(f'slot_list: найдено {slots.count()} свободных слотов')
        return render(request, 'testdrive/slots.html', {'slots': slots})
    except Exception as e:
        logger.error(f'slot_list: ошибка загрузки слотов: {e}', exc_info=True)
        messages.error(request, 'Ошибка при загрузке расписания.')
        return render(request, 'testdrive/slots.html', {'slots': []})


@login_required
def my_bookings(request):
    """Мои записи на тест-драйв."""
    try:
        bookings = TestDriveBooking.objects.filter(
            customer=request.user
        ).select_related('slot__test_car')
        return render(request, 'testdrive/my_list.html', {'bookings': bookings})
    except Exception as e:
        logger.error(f'my_bookings: ошибка загрузки записей: {e}', exc_info=True)
        messages.error(request, 'Ошибка при загрузке ваших записей.')
        return render(request, 'testdrive/my_list.html', {'bookings': []})


@login_required
def booking_detail(request, pk):
    """Просмотр конкретной записи (FR-18)."""
    try:
        booking = get_object_or_404(TestDriveBooking, pk=pk, customer=request.user)
        logger.info(f'booking_detail: пользователь {request.user.username} открыл запись #{pk}')
        return render(request, 'testdrive/detail.html', {'booking': booking})
    except Exception as e:
        logger.error(f'booking_detail: ошибка загрузки записи #{pk}: {e}', exc_info=True)
        messages.error(request, 'Ошибка при загрузке записи.')
        return redirect('testdrive:my_list')


@login_required
def book_slot(request, pk):  # ← ИСПРАВЛЕНО: было slot_id, стало pk
    """Запись на выбранный слот тест-драйва."""
    slot = get_object_or_404(TestDriveSlot, pk=pk)
    
    # Проверка: слот должен быть в будущем и не заблокирован
    if slot.is_blocked or slot.start_time < timezone.now():
        messages.error(request, 'Этот слот недоступен для записи.')
        return redirect('testdrive:slots')
        
    if request.method == 'POST':
        form = TestDriveBookingForm(request.POST)
        
        # ИСПРАВЛЕНИЕ BUG-12: присваиваем значения экземпляру формы ДО вызова is_valid()
        form.instance.customer = request.user
        form.instance.slot = slot
        
        if form.is_valid():
            try:
                # Сохраняем запись
                form.save()
                logger.info(f'УСПЕХ: пользователь {request.user.username} записался на слот #{slot.pk}')
                messages.success(request, 'Вы успешно записались на тест-драйв!')
                return redirect('testdrive:my_list')
            except Exception as e:
                logger.error(f'ОШИБКА при записи на тест-драйв: {type(e).__name__}: {str(e)}', exc_info=True)
                messages.error(request, 'Произошла ошибка при записи. Попробуйте выбрать другой слот.')
        else:
            logger.warning(f'Ошибки валидации формы записи: {form.errors}')
    else:
        form = TestDriveBookingForm()
        
    return render(request, 'testdrive/book.html', {'form': form, 'slot': slot})

@login_required
@require_POST
def booking_cancel(request, pk):
    """FR-07: Отмена записи покупателем."""
    booking = get_object_or_404(TestDriveBooking, pk=pk, customer=request.user)

    if booking.status != 'created':
        logger.warning(
            f'booking_cancel: {request.user.username} попытался отменить запись #{pk} '
            f'в статусе "{booking.status}" — отказано'
        )
        messages.error(
            request,
            f'Нельзя отменить запись в статусе «{booking.get_status_display()}».'
        )
        return redirect('testdrive:my_list')

    try:
        booking.status = 'cancelled'
        booking.save(update_fields=['status'])
        logger.info(
            f'booking_cancel: {request.user.username} отменил запись #{pk} '
            f'(слот #{booking.slot_id}, авто {booking.slot.test_car.internal_number})'
        )
        messages.success(request, 'Запись отменена. Слот снова свободен.')
    except Exception as e:
        logger.error(f'booking_cancel: ошибка при отмене записи #{pk}: {e}', exc_info=True)
        messages.error(request, 'Произошла ошибка при отмене записи.')
        
    return redirect('testdrive:my_list')


@login_required
def booking_status_update(request, pk):
    """FR-08: Менеджер меняет статус."""
    if request.user.role not in ['manager', 'admin']:
        messages.error(request, 'У вас нет прав.')
        return redirect('core:home')
        
    booking = get_object_or_404(TestDriveBooking, pk=pk)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(TestDriveBooking.STATUS_CHOICES):
            try:
                booking.status = new_status
                booking.save(update_fields=['status'])
                
                if booking.customer.email:
                    send_mail(
                        'Статус записи на тест-драйв изменён',
                        f'Ваша запись на {booking.slot.test_car} теперь имеет статус: '
                        f'{booking.get_status_display()}.',
                        'noreply@autodrive.ru',
                        [booking.customer.email],
                        fail_silently=True,
                    )
                logger.info(
                    f'booking_status_update: менеджер {request.user.username} изменил статус '
                    f'записи #{pk} на "{new_status}"'
                )
                messages.success(request, f'Статус изменён на «{booking.get_status_display()}».')
                return redirect('testdrive:manager_list')
            except Exception as e:
                logger.error(f'booking_status_update: ошибка изменения статуса #{pk}: {e}', exc_info=True)
                messages.error(request, 'Произошла ошибка при изменении статуса.')
                
    return render(request, 'testdrive/status_form.html', {'booking': booking})


@login_required
def manager_bookings(request):
    """Панель менеджера."""
    if request.user.role not in ['manager', 'admin']:
        messages.error(request, 'У вас нет прав.')
        return redirect('core:home')
    try:
        bookings = TestDriveBooking.objects.all().select_related('slot__test_car', 'customer', 'slot__manager')
        return render(request, 'testdrive/manager_list.html', {'bookings': bookings})
    except Exception as e:
        logger.error(f'manager_bookings: ошибка загрузки списка: {e}', exc_info=True)
        messages.error(request, 'Ошибка при загрузке списка записей.')
        return render(request, 'testdrive/manager_list.html', {'bookings': []})