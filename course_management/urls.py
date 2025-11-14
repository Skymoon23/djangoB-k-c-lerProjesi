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

        # --- Hoca Learning Outcome & Bileşen & Ağırlık & Not işlemleri ---
    path('instructor/course/<int:course_id>/outcomes/add/', views.add_learning_outcome, name='add_learning_outcome'),
    path('instructor/course/<int:course_id>/components/add/', views.add_evaluation_component, name='add_evaluation_component'),
    path('instructor/component/<int:component_id>/weights/', views.manage_outcome_weights, name='manage_outcome_weights'),
    path('instructor/component/<int:component_id>/grade/add/', views.add_grade, name='add_grade'),
    
    path('student/course/<int:course_id>/', views.student_course_detail, name='student_course_detail'),

]