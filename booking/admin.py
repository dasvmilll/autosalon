from django.contrib import admin
from .models import CarReservation

@admin.register(CarReservation)
class CarReservationAdmin(admin.ModelAdmin):
    list_display = ('car', 'customer', 'status', 'deposit_amount', 'expires_at')
    list_filter = ('status',)
    filter_horizontal = ('additional_equipment',)