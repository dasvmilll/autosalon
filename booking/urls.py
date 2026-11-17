from django.urls import path
from . import views

app_name = 'booking'

urlpatterns = [
    path('my/', views.my_reservations, name='my_list'),
]