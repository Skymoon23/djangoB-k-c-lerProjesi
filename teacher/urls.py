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
        name="manage_component_weights",
    ),
    path(
        "course/<int:course_id>/manage-component-outcomes/",
        views.manage_component_weights,
        name="manage_course_component_weights",

    ),
    path(
        'course/<int:course_id>/upload-grades/',
        views.upload_grades,
        name='upload_grades'  # Bu ismi, 'redirect' fonksiyonunda kullandık.
    ),

    

   path("course/<int:course_id>/", views.course_home, name="course_home"),
   path("course/<int:course_id>/outcomes/", views.course_outcomes, name="course_lo_add"),
   path("course/<int:course_id>/components/", views.course_components, name="course_eval_add"),
   path("course/<int:course_id>/weights/", views.course_weights, name="course_weights"),
   path("course/<int:course_id>/csv-upload/", views.instructor_csv_upload_placeholder, name="instructor_csv_upload_placeholder"),

]
