from django.urls import path
from . import views

urlpatterns = [
    # giriş yönlendiricisi --> settings.pydeki dashboard_redirect burayı kullanır
    path('', views.home, name='home'),
    # giriş yönlendiricisi --> settings.pydeki dashboard_redirect burayı kullanır
    path('dashboard/', views.dashboard_redirect, name='dashboard_redirect'),

    # hoca paneli
    path('instructor/dashboard/', views.instructor_dashboard, name='instructor_dashboard'),

    # öğrenci paneli
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),

    # YENİ bölüm Başkanı Paneli
    path('department/dashboard/', views.department_head_dashboard, name='department_head_dashboard'),

    # ders yönetim sayfası
    path('course/<int:course_id>/manage/', views.manage_course, name='manage_course'),
]