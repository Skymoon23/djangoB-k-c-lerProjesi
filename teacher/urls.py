from django.urls import path

from . import views

urlpatterns = [
    path("dashboard/", views.instructor_dashboard, name="instructor_dashboard"),
    path("course/<int:course_id>/manage/", views.manage_course, name="manage_course"),
    path(
        "course/<int:course_id>/outcomes/add/",
        views.add_learning_outcome,
        name="add_learning_outcome",
    ),
    path(
        "course/<int:course_id>/components/add/",
        views.add_evaluation_component,
        name="add_evaluation_component",
    ),
    path(
        "component/<int:component_id>/weights/",
        views.manage_outcome_weights,
        name="manage_outcome_weights",
    ),
    path(
        "component/<int:component_id>/grade/add/",
        views.add_grade,
        name="add_grade",
    ),
    path(
        "manage-component-outcomes/",
        views.manage_component_weights,
        name="instructor_manage_component_outcomes",
    ),
    path(
        "course/<int:course_id>/manage-component-outcomes/",
        views.manage_component_weights,
        name="instructor_manage_course_component_outcomes",
    ),
    path(
        'upload-grades/',
        views.upload_grades,
        name='upload_grades'  # Bu ismi, 'redirect' fonksiyonunda kullandık.
    ),
]


