import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.views.decorators.http import require_POST
from .models import TestDriveSlot, TestDriveBooking
from .forms import TestDriveBookingForm

logger = logging.getLogger(__name__)


def slot_list(request):
    """Список свободных слотов."""
    slots = TestDriveSlot.objects.filter(
        is_blocked=False,
        start_time__gte=timezone.now()
    ).order_by('start_time')
    return render(request, 'testdrive/slots.html', {'slots': slots})


@login_required
def my_bookings(request):
    """Мои записи на тест-драйв."""
    bookings = TestDriveBooking.objects.filter(
        customer=request.user
    ).select_related('slot__test_car')
    return render(request, 'testdrive/my_list.html', {'bookings': bookings})


@login_required
def booking_detail(request, pk):
    """Просмотр конкретной записи (FR-18)."""
    booking = get_object_or_404(TestDriveBooking, pk=pk, customer=request.user)
    logger.info(f'booking_detail: пользователь {request.user.username} открыл запись #{pk}')
    return render(request, 'testdrive/detail.html', {'booking': booking})


@login_required
def book_slot(request, pk):
    """Запись на тест-драйв."""
    slot = get_object_or_404(TestDriveSlot, pk=pk)
    logger.info(f'book_slot: пользователь {request.user.username} открыл форму записи на слот #{pk}')
    
    if request.method == 'POST':
        form = TestDriveBookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.customer = request.user
            booking.slot = slot
            try:
                booking.full_clean()
            except ValidationError as e:
                for field, errors in e.message_dict.items():
                    for error in errors:
                        form.add_error(field if field != '__all__' else None, error)
                logger.warning(f'book_slot: ошибки модели при записи на слот #{pk}: {e}')
            else:
                booking.save()
                logger.info(
                    f'book_slot: УСПЕХ — {request.user.username} записался на тест-драйв '
                    f'(слот #{pk}, авто {slot.test_car.internal_number}, '
                    f'ВУ {booking.license_number}, стаж {booking.experience_years} лет)'
                )
                messages.success(request, 'Вы успешно записались на тест-драйв!')
                return redirect('testdrive:my_list')
    else:
        form = TestDriveBookingForm(initial={'slot': slot})
        form.fields['slot'].queryset = TestDriveSlot.objects.filter(pk=slot.pk)
    
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
    
    booking.status = 'cancelled'
    booking.save(update_fields=['status'])
    logger.info(
        f'booking_cancel: {request.user.username} отменил запись #{pk} '
        f'(слот #{booking.slot_id}, авто {booking.slot.test_car.internal_number})'
    )
    messages.success(request, 'Запись отменена. Слот снова свободен.')
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
    return render(request, 'testdrive/status_form.html', {'booking': booking})


@login_required
def manager_bookings(request):
    """Панель менеджера."""
    if request.user.role not in ['manager', 'admin']:
        messages.error(request, 'У вас нет прав.')
        return redirect('core:home')
    # ИСПРАВЛЕНИЕ N+1: добавлен select_related
    bookings = TestDriveBooking.objects.all().select_related('slot__test_car', 'customer', 'slot__manager')
    return render(request, 'testdrive/manager_list.html', {'bookings': bookings})