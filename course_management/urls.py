from django.urls import path
from . import views

urlpatterns = [
    # giriş yönlendiricisi --> settings.pydeki dashboard_redirect burayı kullanır
    path('dashboard/', views.dashboard_redirect, name='dashboard_redirect'),

    # hoca Paneli
    path('instructor/dashboard/', views.instructor_dashboard, name='instructor_dashboard'),

    # öğrenci Paneli
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),

    # ders Yönetim Sayfası
    path('course/<int:course_id>/manage/', views.manage_course, name='manage_course'),
]