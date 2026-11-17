from django.urls import path
from . import views

app_name = 'testdrive'

urlpatterns = [
    path('slots/', views.slot_list, name='slots'),
    path('my/', views.my_bookings, name='my_list'),
]