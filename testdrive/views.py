from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import TestDriveSlot, TestDriveBooking

def slot_list(request):
    slots = TestDriveSlot.objects.filter(is_blocked=False, start_time__gte=timezone.now()).order_by('start_time')
    return render(request, 'testdrive/slots.html', {'slots': slots})

@login_required
def my_bookings(request):
    bookings = TestDriveBooking.objects.filter(customer=request.user).select_related('slot__test_car')
    return render(request, 'testdrive/my_list.html', {'bookings': bookings})