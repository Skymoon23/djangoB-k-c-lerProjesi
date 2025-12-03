from django.urls import path

from . import views

urlpatterns = [
    # giriş yönlendiricisi --> settings.pydeki dashboard_redirect burayı kullanır
    path('', views.home, name='home'),
    # giriş yönlendiricisi --> settings.pydeki dashboard_redirect burayı kullanır
    path('dashboard/', views.dashboard_redirect, name='dashboard_redirect'),
]