from django.urls import path

from . import views

urlpatterns = [
    path("dashboard/", views.department_head_dashboard, name="department_head_dashboard"),
    path(
        "manage-lo-po-weights/",
        views.manage_lo_po_weights,
        name="manage_lo_po_weights",
    ),
    path(
        "view-outcomes/",
        views.view_outcomes,
        name="view_outcomes",
    ),
    path(
        "program-outcome-achievement/",
        views.po_achievement,
        name="po_achievement",
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


