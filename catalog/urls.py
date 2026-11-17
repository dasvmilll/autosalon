from django.urls import path
from . import views

app_name = 'catalog'

urlpatterns = [
    path('', views.catalog_list, name='list'),
    path('car/<int:pk>/', views.car_detail, name='detail'),
]