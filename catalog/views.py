from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from .models import CarInStock
from django.http import JsonResponse
from django.db.models import Q

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

def api_search(request):
    query = request.GET.get('q', '')
    if query:
        cars = CarInStock.objects.filter(
            Q(trim__car_model__brand__icontains=query) | 
            Q(trim__car_model__name__icontains=query),
            status='available'
        )[:5]
        data = [{'id': c.id, 'name': f'{c.trim.car_model.brand} {c.trim.car_model.name}', 'price': float(c.actual_price)} for c in cars]
        return JsonResponse({'results': data})
    return JsonResponse({'results': []})

def api_filter_cars(request):
    cars = CarInStock.objects.filter(status='available').select_related('trim__car_model')
    
    brand_query = request.GET.get('brand', '')
    if brand_query:
        cars = cars.filter(trim__car_model__brand__icontains=brand_query)
        
    sort = request.GET.get('sort', '')
    if sort == 'price_asc':
        cars = cars.order_by('actual_price')
    elif sort == 'price_desc':
        cars = cars.order_by('-actual_price')
    else:
        cars = cars.order_by('-arrival_date')

    cars = cars[:20]

    # Словарь картинок (должен совпадать с custom_filters.py)
    images = {
        'haval': '/media/cars/haval.jpg',
        'chery': '/media/cars/chery.jpg',
        'geely': '/media/cars/geely.jpg',
        'lada': '/media/cars/lada.jpg',
        'hyundai': '/media/cars/hyundai.jpg',
    }

    data = []
    for car in cars:
        brand_key = car.trim.car_model.brand.lower()
        image_url = images.get(brand_key, '/media/cars/haval.jpg')  # локальная картинка
        
        data.append({
            'id': car.id,
            'brand': car.trim.car_model.brand,
            'model': car.trim.car_model.name,
            'trim': car.trim.name,
            'color': car.color,
            'price': float(car.actual_price),
            'image': image_url,
            'status': car.status,
        })

    return JsonResponse({'cars': data})