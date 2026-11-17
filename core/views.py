from django.shortcuts import render
from catalog.models import CarInStock

def home(request):
    cars = CarInStock.objects.filter(status='available')[:3]
    return render(request, 'core/home.html', {'cars': cars})