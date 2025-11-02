from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),

    # zoomda bahsettiğim hazır giriş/çıkış sistemi, django direkt sağlıyor ayarları da settings.py dan yönetebiliyoruz
    path('accounts/', include('django.contrib.auth.urls')),

    # app URL si
    path('', include('course_management.urls')),
]
