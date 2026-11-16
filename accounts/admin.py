from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'role', 'driving_experience_years', 'is_staff')
    list_filter = ('role', 'is_staff', 'is_superuser')
    fieldsets = (
        ('Данные автосалона', {
            'fields': ('role', 'phone', 'driver_license', 'driving_experience_years')
        }),
    ) + UserAdmin.fieldsets