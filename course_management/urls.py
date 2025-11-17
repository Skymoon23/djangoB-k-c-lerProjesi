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
    path('instructor/manage-component-outcomes/', views.instructor_manage_component_outcomes, name='instructor_manage_component_outcomes'),
    path('instructor/course/<int:course_id>/manage-component-outcomes/', views.instructor_manage_component_outcomes, name='instructor_manage_course_component_outcomes'),
    
    path('student/course/<int:course_id>/', views.student_course_detail, name='student_course_detail'),
    
    path('department/manage-lo-po-weights/', views.department_head_manage_lo_po_weights, name='department_head_manage_lo_po_weights'),
    path('department/view-outcomes/', views.department_head_view_outcomes, name='department_head_view_outcomes'),
    path('department/program-outcome-achievement/', views.department_head_program_outcome_achievement, name='department_head_program_outcome_achievement'),
    path('department/program-outcome/<int:outcome_id>/delete/', views.delete_program_outcome, name='delete_program_outcome'),
    path('department/program-outcome/<int:outcome_id>/edit/', views.edit_program_outcome, name='edit_program_outcome'),

]