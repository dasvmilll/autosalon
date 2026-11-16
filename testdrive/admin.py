from django.contrib import admin
from .models import TestCar, TestDriveSlot, TestDriveBooking

@admin.register(TestCar)
class TestCarAdmin(admin.ModelAdmin):
    list_display = ('internal_number', 'model_ref', 'plate_number', 'is_active')

@admin.register(TestDriveSlot)
class TestDriveSlotAdmin(admin.ModelAdmin):
    list_display = ('test_car', 'manager', 'start_time', 'end_time', 'is_blocked')
    list_filter = ('test_car', 'manager')

@admin.register(TestDriveBooking)
class TestDriveBookingAdmin(admin.ModelAdmin):
    list_display = ('customer', 'slot', 'status', 'experience_years')
    list_filter = ('status',)