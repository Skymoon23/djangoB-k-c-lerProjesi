from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from course_management.decorators import user_is_department_head
from course_management.forms import (
    CourseCreateForm,
    InstructorAssignForm,
    ProgramOutcomeForm,
    StudentAssignForm,
)
from course_management.models import (
    Course,
    Grade,
    LearningOutcome,
    LearningOutcomeProgramOutcomeWeight,
    OutcomeWeight,
    ProgramOutcome,
    User,
)


@login_required
@user_is_department_head
def department_head_dashboard(request):
    """
    Bölüm başkanının paneli.
    Önceki implementasyon course_management.views içinden taşındı.
    """
    if request.method == "POST":
        if "submit_course_create" in request.POST:
            course_form = CourseCreateForm(request.POST)
            assign_form = InstructorAssignForm()
            student_assign_form = StudentAssignForm()

            if course_form.is_valid():
                course_form.save()
                messages.success(request, "Yeni ders başarıyla eklendi.")
                return redirect("department_head_dashboard")
            messages.error(
                request,
                "Ders eklenirken bir hata oluştu. Lütfen formu kontrol edin.",
            )

        elif "submit_instructor_assign" in request.POST:
            assign_form = InstructorAssignForm(request.POST)
            course_form = CourseCreateForm()
            student_assign_form = StudentAssignForm()

            if assign_form.is_valid():
                course = assign_form.cleaned_data["course"]
                instructor = assign_form.cleaned_data["instructor"]

                course.instructors.add(instructor)

                messages.success(
                    request,
                    f'"{instructor.get_full_name()}" hocası "{course.course_code}" dersine başarıyla atandı.',
                )
                return redirect("department_head_dashboard")
            messages.error(
                request,
                "Hoca atanırken bir hata oluştu. Lütfen formu kontrol edin.",
            )

        elif "submit_student_assign" in request.POST:
            student_assign_form = StudentAssignForm(request.POST)
            course_form = CourseCreateForm()
            assign_form = InstructorAssignForm()

            if student_assign_form.is_valid():
                course = student_assign_form.cleaned_data["course"]
                student = student_assign_form.cleaned_data["student"]

                course.students.add(student)

                messages.success(
                    request,
                    f'"{student.get_full_name()}" öğrencisi "{course.course_code}" dersine başarıyla atandı.',
                )
                return redirect("department_head_dashboard")
            messages.error(
                request,
                "Öğrenci atanırken bir hata oluştu. Lütfen formu kontrol edin.",
            )

        elif "submit_program_outcome" in request.POST:
            program_outcome_form = ProgramOutcomeForm(request.POST)
            course_form = CourseCreateForm()
            assign_form = InstructorAssignForm()
            student_assign_form = StudentAssignForm()

            if program_outcome_form.is_valid():
                program_outcome_form.save()
                messages.success(
                    request,
                    "Yeni program çıktısı başarıyla eklendi.",
                )
                return redirect("department_head_dashboard")
            messages.error(
                request,
                "Program çıktısı eklenirken bir hata oluştu.",
            )

        else:
            course_form = CourseCreateForm()
            assign_form = InstructorAssignForm()
            student_assign_form = StudentAssignForm()
            program_outcome_form = ProgramOutcomeForm()
    else:
        course_form = CourseCreateForm()
        assign_form = InstructorAssignForm()
        student_assign_form = StudentAssignForm()
        program_outcome_form = ProgramOutcomeForm()

    all_courses = Course.objects.all().prefetch_related("instructors").order_by(
        "course_code"
    )

    all_instructors = User.objects.filter(
        profile__role="instructor",
    ).order_by("last_name", "first_name")
    all_students = User.objects.filter(
        profile__role="student",
    ).prefetch_related("enrolled_courses").order_by("last_name", "first_name")
    all_program_outcomes = ProgramOutcome.objects.all()

    context = {
        "all_courses": all_courses,
        "all_instructors": all_instructors,
        "all_students": all_students,
        "course_count": all_courses.count(),
        "instructor_count": all_instructors.count(),
        "student_count": all_students.count(),
        "course_form": course_form,
        "assign_form": assign_form,
        "student_assign_form": student_assign_form,
        "program_outcome_form": program_outcome_form,
        "all_program_outcomes": all_program_outcomes,
    }

    return render(request, "headteacher/department_head_dashboard.html", context)


@login_required
@user_is_department_head
def department_head_manage_lo_po_weights(request):
    all_courses = Course.objects.all().prefetch_related("learning_outcomes")
    all_program_outcomes = ProgramOutcome.objects.all().order_by("code")

    course_data = []
    for course in all_courses:
        outcomes = course.learning_outcomes.all()

        outcome_data = []
        for outcome in outcomes:
            existing_weights = LearningOutcomeProgramOutcomeWeight.objects.filter(
                learning_outcome=outcome
            )
            weight_map = {
                w.program_outcome_id: w.weight for w in existing_weights
            }

            po_rows = []
            for po in all_program_outcomes:
                po_rows.append(
                    {
                        "program_outcome": po,
                        "weight": weight_map.get(po.id),
                    }
                )

            outcome_data.append(
                {
                    "outcome": outcome,
                    "po_rows": po_rows,
                }
            )

        course_data.append(
            {
                "course": course,
                "outcome_data": outcome_data,
            }
        )

    if request.method == "POST":
        outcome_id = request.POST.get("outcome_id")
        outcome = get_object_or_404(LearningOutcome, id=outcome_id)

        for po in all_program_outcomes:
            field_name = f"weight_{outcome_id}_{po.id}"
            value = request.POST.get(field_name)

            if value:
                value_int = int(value)
                LearningOutcomeProgramOutcomeWeight.objects.update_or_create(
                    learning_outcome=outcome,
                    program_outcome=po,
                    defaults={"weight": value_int},
                )
            else:
                LearningOutcomeProgramOutcomeWeight.objects.filter(
                    learning_outcome=outcome,
                    program_outcome=po,
                ).delete()

        messages.success(request, "Ağırlıklar başarıyla güncellendi.")
        return redirect("department_head_manage_lo_po_weights")

    context = {
        "course_data": course_data,
        "all_program_outcomes": all_program_outcomes,
    }
    return render(request, "headteacher/department_head_manage_lo_po_weights.html", context)


@login_required
@user_is_department_head
def department_head_view_outcomes(request):
    all_courses = Course.objects.all().prefetch_related(
        "learning_outcomes",
        "evaluation_components",
    )
    all_program_outcomes = ProgramOutcome.objects.all().order_by("code")

    course_data = []
    for course in all_courses:
        components = course.evaluation_components.all()
        outcomes = course.learning_outcomes.all()

        component_lo_data = []
        for component in components:
            weights = OutcomeWeight.objects.filter(
                component=component
            ).select_related("outcome")
            component_lo_data.append(
                {
                    "component": component,
                    "weights": weights,
                }
            )

        lo_po_data = []
        for outcome in outcomes:
            weights = LearningOutcomeProgramOutcomeWeight.objects.filter(
                learning_outcome=outcome
            ).select_related("program_outcome")
            lo_po_data.append(
                {
                    "outcome": outcome,
                    "weights": weights,
                }
            )

        course_data.append(
            {
                "course": course,
                "component_lo_data": component_lo_data,
                "lo_po_data": lo_po_data,
            }
        )

    context = {
        "course_data": course_data,
        "all_program_outcomes": all_program_outcomes,
    }
    return render(request, "headteacher/department_head_view_outcomes.html", context)


@login_required
@user_is_department_head
def department_head_program_outcome_achievement(request):
    all_courses = Course.objects.all().prefetch_related(
        "learning_outcomes",
        "evaluation_components",
        "students",
    )
    all_program_outcomes = ProgramOutcome.objects.all().order_by("code")
    all_students = User.objects.filter(
        profile__role="student",
    ).prefetch_related("enrolled_courses", "grades")

    all_grades = Grade.objects.select_related("student", "component").filter(
        student__profile__role="student",
        score__isnull=False,
    )
    grade_map = {(g.student_id, g.component_id): g.score for g in all_grades}

    all_outcome_weights = OutcomeWeight.objects.select_related(
        "component",
        "outcome",
    ).all()
    comp_lo_weight_map = {
        (w.component_id, w.outcome_id): w.weight for w in all_outcome_weights
    }

    all_lo_po_weights = LearningOutcomeProgramOutcomeWeight.objects.select_related(
        "learning_outcome",
        "program_outcome",
    ).all()
    lo_po_weight_map = {
        (w.learning_outcome_id, w.program_outcome_id): w.weight
        for w in all_lo_po_weights
    }

    po_achievement_data = []

    for po in all_program_outcomes:
        student_po_scores = []

        for student in all_students:
            student_po_score = Decimal("0.0")
            student_po_weight = Decimal("0.0")

            for course in all_courses:
                if student not in course.students.all():
                    continue

                components = list(course.evaluation_components.all())
                outcomes = list(course.learning_outcomes.all())

                for outcome in outcomes:
                    lo_po_weight = lo_po_weight_map.get((outcome.id, po.id))
                    if not lo_po_weight:
                        continue

                    lo_weight_to_po = Decimal(lo_po_weight)

                    lo_weighted_score = Decimal("0.0")
                    lo_total_weight = Decimal("0.0")

                    for component in components:
                        grade_score = grade_map.get((student.id, component.id))
                        if grade_score is None:
                            continue

                        comp_lo_weight = comp_lo_weight_map.get(
                            (component.id, outcome.id)
                        )
                        if not comp_lo_weight:
                            continue

                        comp_weight_to_lo = Decimal(comp_lo_weight)
                        lo_weighted_score += Decimal(grade_score) * comp_weight_to_lo
                        lo_total_weight += comp_weight_to_lo

                    if lo_total_weight > 0:
                        lo_score = lo_weighted_score / lo_total_weight
                        student_po_score += lo_score * lo_weight_to_po
                        student_po_weight += lo_weight_to_po

            if student_po_weight > 0:
                final_po_score = student_po_score / student_po_weight
                student_po_scores.append(float(final_po_score))

        if student_po_scores:
            average_score = sum(student_po_scores) / len(student_po_scores)
            min_score = min(student_po_scores)
            max_score = max(student_po_scores)
            student_count = len(student_po_scores)
        else:
            average_score = 0
            min_score = 0
            max_score = 0
            student_count = 0

        po_achievement_data.append(
            {
                "program_outcome": po,
                "average_score": average_score,
                "min_score": min_score,
                "max_score": max_score,
                "student_count": student_count,
            }
        )

    context = {
        "po_achievement_data": po_achievement_data,
    }
    return render(request, "headteacher/department_head_program_outcome_achievement.html", context)


@login_required
@user_is_department_head
def delete_program_outcome(request, outcome_id):
    program_outcome = get_object_or_404(ProgramOutcome, id=outcome_id)

    if request.method == "POST":
        program_outcome.delete()
        messages.success(
            request,
            f'"{program_outcome.code}" program outcome\'ı başarıyla silindi.',
        )
    else:
        messages.error(
            request,
            "Program outcome silme isteği başarısız oldu.",
        )

    return redirect("department_head_dashboard")


@login_required
@user_is_department_head
def edit_program_outcome(request, outcome_id):
    program_outcome = get_object_or_404(ProgramOutcome, id=outcome_id)

    if request.method == "POST":
        form = ProgramOutcomeForm(request.POST, instance=program_outcome)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                f'"{program_outcome.code}" program outcome\'ı güncellendi.',
            )
            return redirect("department_head_dashboard")
        messages.error(
            request,
            "Program outcome güncellenirken bir hata oluştu. Lütfen formu kontrol edin.",
        )
    else:
        form = ProgramOutcomeForm(instance=program_outcome)

    context = {
        "form": form,
        "program_outcome": program_outcome,
    }
    return render(request, "headteacher/edit_program_outcome.html", context)


