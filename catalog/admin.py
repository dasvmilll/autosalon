from django.contrib import admin
from .models import CarModel, Trim, CarInStock, AdditionalEquipment

@admin.register(CarModel)
class CarModelAdmin(admin.ModelAdmin):
    list_display = ('brand', 'name', 'body_type')

@admin.register(Trim)
class TrimAdmin(admin.ModelAdmin):
    list_display = ('car_model', 'name', 'price')

@admin.register(CarInStock)
class CarInStockAdmin(admin.ModelAdmin):
    list_display = ('vin', 'trim', 'color', 'status', 'actual_price')
    list_filter = ('status', 'trim__car_model__brand')
    search_fields = ('vin',)

@admin.register(AdditionalEquipment)
class AdditionalEquipmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'price')