from django.urls import path

from . import views

urlpatterns = [
    path("dashboard/", views.department_head_dashboard, name="department_head_dashboard"),
    path(
        "manage-lo-po-weights/",
        views.department_head_manage_lo_po_weights,
        name="department_head_manage_lo_po_weights",
    ),
    path(
        "view-outcomes/",
        views.department_head_view_outcomes,
        name="department_head_view_outcomes",
    ),
    path(
        "program-outcome-achievement/",
        views.department_head_program_outcome_achievement,
        name="department_head_program_outcome_achievement",
    ),
    path(
        "program-outcome/<int:outcome_id>/delete/",
        views.delete_program_outcome,
        name="delete_program_outcome",
    ),
    path(
        "program-outcome/<int:outcome_id>/edit/",
        views.edit_program_outcome,
        name="edit_program_outcome",
    ),
]


