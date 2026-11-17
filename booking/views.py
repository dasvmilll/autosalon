from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import CarReservation

@login_required
def my_reservations(request):
    reservations = CarReservation.objects.filter(customer=request.user).select_related('car__trim__car_model')
    return render(request, 'booking/my_list.html', {'reservations': reservations})