from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path("dashboard/", views.department_head_dashboard, name="department_head_dashboard"),

    # Sidebar pages
    path("quick-actions/", views.department_head_quick_actions, name="department_head_quick_actions"),
    path("outcomes/", views.department_head_outcomes_menu, name="department_head_outcomes_menu"),

    path("courses/", views.department_head_courses, name="department_head_courses"),
    path("program-outcomes/", views.department_head_program_outcomes, name="department_head_program_outcomes"),
    path("instructors/", views.department_head_instructors, name="department_head_instructors"),
    path("students/", views.department_head_students, name="department_head_students"),

    # Program Outcome actions
    path("program-outcome/create/", views.department_head_create_program_outcome, name="department_head_create_program_outcome"),
    path("program-outcome/<int:outcome_id>/edit/", views.edit_program_outcome, name="edit_program_outcome"),
    path("program-outcome/<int:outcome_id>/delete/", views.delete_program_outcome, name="delete_program_outcome"),
    path("learning-outcome/<int:outcome_id>/edit/", views.edit_learning_outcome, name="edit_learning_outcome"),
    path("learning-outcome/<int:outcome_id>/delete/", views.delete_learning_outcome, name="delete_learning_outcome"),

    # Analytics / reports
    path("manage-lo-po-weights/", views.manage_lo_po_weights, name="manage_lo_po_weights"),
    path("view-outcomes/", views.view_outcomes, name="view_outcomes"),
    path("program-outcome-achievement/", views.po_achievement, name="po_achievement"),


    path(
    "instructors/<int:instructor_id>/edit/",
    views.edit_instructor_courses,
    name="edit_instructor_courses"
),


path(
    "students/<int:student_id>/edit/",
    views.edit_student_courses,
    name="edit_student_courses",
),
path(
    "students/<int:student_id>/delete/",
    views.delete_student,
    name="delete_student",
),
]
