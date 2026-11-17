from django.urls import path
from . import views

app_name = 'tradein'

urlpatterns = [
    path('my/', views.my_tradeins, name='my_list'),
]