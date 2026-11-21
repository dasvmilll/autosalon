from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from .models import CarInStock
from django.http import JsonResponse
from django.db.models import Q
import logging

logger = logging.getLogger(__name__)


def catalog_list(request):
    """Список автомобилей с фильтрацией и сортировкой."""
    logger.info(f'catalog_list: открытие каталога, параметры: {dict(request.GET)}')
    cars = CarInStock.objects.filter(status='available').select_related('trim__car_model')
    
    brand_query = request.GET.get('brand')
    if brand_query:
        cars = cars.filter(trim__car_model__brand__icontains=brand_query)
    
    body_query = request.GET.get('body')
    if body_query:
        cars = cars.filter(trim__car_model__body_type__icontains=body_query)
    
    # ИСПРАВЛЕНИЕ BUG-13: защита от нечисловых значений цены
    price_max = request.GET.get('price_max')
    if price_max:
        try:
            cars = cars.filter(actual_price__lte=float(price_max))
        except (ValueError, TypeError):
            logger.warning(f'catalog_list: некорректное значение price_max="{price_max}"')
    
    price_min = request.GET.get('price_min')
    if price_min:
        try:
            cars = cars.filter(actual_price__gte=float(price_min))
        except (ValueError, TypeError):
            logger.warning(f'catalog_list: некорректное значение price_min="{price_min}"')
    
    sort = request.GET.get('sort')
    if sort == 'price_asc':
        cars = cars.order_by('actual_price')
    elif sort == 'price_desc':
        cars = cars.order_by('-actual_price')
    elif sort == 'date_new':
        cars = cars.order_by('-arrival_date')
    elif sort == 'date_old':
        cars = cars.order_by('arrival_date')
    else:
        cars = cars.order_by('-arrival_date')
    
    paginator = Paginator(cars, 20)
    page_obj = paginator.get_page(request.GET.get('page'))
    
    logger.info(f'catalog_list: найдено {paginator.count} машин, страница {page_obj.number}')
    return render(request, 'catalog/list.html', {'page_obj': page_obj, 'cars': page_obj.object_list})

def car_detail(request, pk):
    """Детальная страница автомобиля."""
    # ИСПРАВЛЕНИЕ: добавлен select_related для загрузки связанных объектов одним JOIN-запросом
    # Раньше: 1 запрос на машину + 1 на trim + 1 на car_model = 3 запроса
    # Теперь: 1 запрос с JOIN
    car = get_object_or_404(
        CarInStock.objects.select_related('trim__car_model'),
        pk=pk
    )
    logger.info(f'car_detail: открыта карточка авто #{pk} ({car.trim.car_model.brand} {car.trim.car_model.name})')
    return render(request, 'catalog/detail.html', {'car': car})


def api_search(request):
    """Живой поиск в шапке сайта.
    ИСПРАВЛЕНИЕ BUG-14: добавлен поиск по VIN (требование FR-01).
    """
    query = request.GET.get('q', '').strip()
    logger.debug(f'api_search: запрос "{query}" от {request.META.get("REMOTE_ADDR")}')
    
    if len(query) < 2:
        return JsonResponse([], safe=False)
    
    # ИСПРАВЛЕНИЕ BUG-14: добавлен поиск по VIN
    cars = CarInStock.objects.filter(
        Q(trim__car_model__brand__icontains=query) |
        Q(trim__car_model__name__icontains=query) |
        Q(vin__icontains=query),  # ← ДОБАВЛЕНО
        status='available'
    ).select_related('trim__car_model')[:5]
    
    data = [
        {
            'id': c.id,
            'brand': c.trim.car_model.brand,
            'model': c.trim.car_model.name,
            'price': float(c.actual_price),
        }
        for c in cars
    ]
    
    logger.debug(f'api_search: найдено {len(data)} результатов')
    return JsonResponse(data, safe=False)


def api_filter_cars(request):
    """Живой фильтр каталога.
    ИСПРАВЛЕНИЕ BUG-09: добавлена обработка price_min, price_max и body.
    """
    logger.debug(f'api_filter_cars: параметры фильтра {dict(request.GET)}')
    
    cars = CarInStock.objects.filter(status='available').select_related('trim__car_model')
    
    # Фильтр по бренду
    brand_query = request.GET.get('brand', '')
    if brand_query:
        cars = cars.filter(trim__car_model__brand__icontains=brand_query)
    
    # ИСПРАВЛЕНИЕ BUG-09: фильтр по кузову
    body_query = request.GET.get('body', '')
    if body_query:
        cars = cars.filter(trim__car_model__body_type__icontains=body_query)
    
    # ИСПРАВЛЕНИЕ BUG-09: фильтр по цене (от/до)
    price_min = request.GET.get('price_min', '')
    if price_min:
        try:
            cars = cars.filter(actual_price__gte=float(price_min))
        except (ValueError, TypeError):
            logger.warning(f'api_filter_cars: некорректное значение price_min="{price_min}"')
    
    price_max = request.GET.get('price_max', '')
    if price_max:
        try:
            cars = cars.filter(actual_price__lte=float(price_max))
        except (ValueError, TypeError):
            logger.warning(f'api_filter_cars: некорректное значение price_max="{price_max}"')
    
    # Сортировка
    sort = request.GET.get('sort', '')
    if sort == 'price_asc':
        cars = cars.order_by('actual_price')
    elif sort == 'price_desc':
        cars = cars.order_by('-actual_price')
    else:
        cars = cars.order_by('-arrival_date')
    
    cars = cars[:20]
    
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
        image_url = images.get(brand_key, '/media/cars/default.jpg')
        data.append({
            'id': car.id,
            'brand': car.trim.car_model.brand,
            'model': car.trim.car_model.name,
            'trim': car.trim.name,
            'color': car.color,
            'price': float(car.actual_price),
            'price_formatted': f'{int(car.actual_price):,}'.replace(',', ' '),
            'image': image_url,
            'status': car.status,
            'status_display': car.get_status_display(),
        })
    
    logger.debug(f'api_filter_cars: возвращено {len(data)} машин')
    return JsonResponse({'cars': data})