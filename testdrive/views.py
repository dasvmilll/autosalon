from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import TestDriveSlot, TestDriveBooking
from .forms import TestDriveBookingForm

def slot_list(request):
    slots = TestDriveSlot.objects.filter(is_blocked=False, start_time__gte=timezone.now()).order_by('start_time')
    return render(request, 'testdrive/slots.html', {'slots': slots})

@login_required
def my_bookings(request):
    bookings = TestDriveBooking.objects.filter(customer=request.user).select_related('slot__test_car')
    return render(request, 'testdrive/my_list.html', {'bookings': bookings})

@login_required
def book_slot(request, pk):
    slot = get_object_or_404(TestDriveSlot, pk=pk)
    if request.method == 'POST':
        form = TestDriveBookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.customer = request.user
            booking.slot = slot
            booking.save()
            messages.success(request, 'Вы успешно записались на тест-драйв!')
            return redirect('testdrive:my_list')
    else:
        form = TestDriveBookingForm(initial={'slot': slot})
        form.fields['slot'].queryset = TestDriveSlot.objects.filter(pk=slot.pk)
    return render(request, 'testdrive/book.html', {'form': form, 'slot': slot})