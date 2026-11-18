from django.urls import path
from . import views

app_name = 'catalog'

urlpatterns = [
    path('', views.catalog_list, name='list'),
    path('car/<int:pk>/', views.car_detail, name='detail'),
    path('api/search/', views.api_search, name='api_search'),
    path('api/filter/', views.api_filter_cars, name='api_filter'),
]