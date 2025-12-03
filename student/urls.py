from django.urls import path

from . import views

urlpatterns = [
    path("dashboard/", views.student_dashboard, name="student_dashboard"),
    path("course/<int:course_id>/", views.student_course_detail, name="student_course_detail"),
]


