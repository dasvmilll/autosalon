from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),  # Главная
    path('catalog/', include('catalog.urls')), # Каталог
    path('testdrive/', include('testdrive.urls')), # Тест-драйв
    path('booking/', include('booking.urls')), # Брони
    path('tradein/', include('tradein.urls')), # Трейд-ин
    path('accounts/', include('django.contrib.auth.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)