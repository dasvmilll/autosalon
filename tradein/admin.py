from django.contrib import admin
from .models import TradeInRequest

@admin.register(TradeInRequest)
class TradeInRequestAdmin(admin.ModelAdmin):
    list_display = ('brand', 'model_name', 'customer', 'year', 'status', 'preliminary_estimate')
    list_filter = ('status',)