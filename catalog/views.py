from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from .models import CarInStock

def catalog_list(request):
    cars = CarInStock.objects.filter(status='available').select_related('trim__car_model')
    
    brand_query = request.GET.get('brand')
    if brand_query:
        cars = cars.filter(trim__car_model__brand__icontains=brand_query)
        
    sort = request.GET.get('sort')
    if sort == 'price_asc':
        cars = cars.order_by('actual_price')
    elif sort == 'price_desc':
        cars = cars.order_by('-actual_price')
    else:
        cars = cars.order_by('-arrival_date')

    paginator = Paginator(cars, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'catalog/list.html', {'page_obj': page_obj, 'cars': page_obj.object_list})

def car_detail(request, pk):
    car = get_object_or_404(CarInStock, pk=pk)
    return render(request, 'catalog/detail.html', {'car': car})