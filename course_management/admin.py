from django.contrib import admin
from .models import Profile, Course, EvaluationComponent, LearningOutcome, Grade


# admin paneli
class CourseAdmin(admin.ModelAdmin):
    list_display = ('course_code', 'course_name')
    search_fields = ('course_code', 'course_name')
    filter_horizontal = ('instructors', 'students',)


admin.site.register(Course, CourseAdmin)
admin.site.register(Profile)
admin.site.register(EvaluationComponent)
admin.site.register(LearningOutcome)
admin.site.register(Grade)
