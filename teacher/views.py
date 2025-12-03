from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from course_management.decorators import user_is_instructor
from course_management.forms import (
    EvaluationComponentForm,
    GradeForm,
    LearningOutcomeForm,
    SyllabusForm,
)
from course_management.models import (
    Course,
    EvaluationComponent,
    Grade,
    LearningOutcome,
    OutcomeWeight,
)


@login_required
@user_is_instructor
def instructor_dashboard(request):
    """
    Giriş yapan hocanın derslerim sayfasını gösterir.
    Önceki implementasyon course_management.views içinden taşındı.
    """
    courses = Course.objects.filter(instructors=request.user)
    context = {"courses": courses}
    return render(request, "teacher/instructor_dashboard.html", context)


@login_required
@user_is_instructor
def manage_course(request, course_id):
    """
    Hocanın ders yönettiği sayfa (çoklu form yönetimi).
    Önceki implementasyon course_management.views içinden taşındı.
    """
    course = get_object_or_404(Course, id=course_id, instructors=request.user)
    components = EvaluationComponent.objects.filter(course=course).order_by("id")
    outcomes = LearningOutcome.objects.filter(course=course)
    students = course.students.all().order_by("last_name", "first_name")

    syllabus_form = SyllabusForm(instance=course)
    eval_form = EvaluationComponentForm()
    outcome_form = LearningOutcomeForm()

    if request.method == "POST":
        if "submit_evaluation" in request.POST:
            eval_form = EvaluationComponentForm(request.POST)
            if eval_form.is_valid():
                evaluation = eval_form.save(commit=False)
                evaluation.course = course
                evaluation.save()
                messages.success(request, "Değerlendirme bileşeni başarıyla eklendi.")
                return redirect("manage_course", course_id=course.id)

        elif "submit_outcome" in request.POST:
            outcome_form = LearningOutcomeForm(request.POST)
            if outcome_form.is_valid():
                outcome = outcome_form.save(commit=False)
                outcome.course = course
                outcome.save()
                messages.success(request, "Öğrenim çıktısı başarıyla eklendi.")
                return redirect("manage_course", course_id=course.id)

        elif "submit_syllabus" in request.POST:
            syllabus_form = SyllabusForm(
                request.POST,
                request.FILES,
                instance=course,
            )
            if syllabus_form.is_valid():
                syllabus_form.save()
                messages.success(request, "Syllabus dosyası başarıyla güncellendi.")
                return redirect("manage_course", course_id=course.id)
            else:
                messages.error(
                    request,
                    "Dosya yüklenirken bir hata oluştu. Lütfen geçerli bir dosya seçin.",
                )

        elif "submit_grades" in request.POST:
            try:
                for key, value in request.POST.items():
                    if not key.startswith("grade_"):
                        continue
                    parts = key.split("_")
                    if len(parts) != 3:
                        continue
                    _, student_id, component_id = parts

                    score_value = value.strip() if value else None

                    if score_value:
                        try:
                            score_decimal = Decimal(score_value)
                            if score_decimal < 0 or score_decimal > 100:
                                continue
                        except (ValueError, InvalidOperation):
                            continue
                    else:
                        score_decimal = None

                    grade, _ = Grade.objects.get_or_create(
                        student_id=student_id,
                        component_id=component_id,
                    )
                    grade.score = score_decimal
                    grade.save()
                messages.success(request, "Notlar başarıyla kaydedildi.")
            except (ValueError, Exception) as e:
                messages.error(
                    request,
                    f"Notları kaydederken bir hata oluştu: {e}",
                )
            return redirect("manage_course", course_id=course.id)

    all_grades = Grade.objects.filter(
        component__in=components,
        student__in=students,
    )
    grade_map = {
        (g.student_id, g.component_id): g.score for g in all_grades
    }

    student_grade_rows = []
    for student in students:
        row = {
            "student_object": student,
            "grades_list": [],
        }
        for component in components:
            score = grade_map.get((student.id, component.id))
            row["grades_list"].append(
                {
                    "component_id": component.id,
                    "score": score,
                }
            )
        student_grade_rows.append(row)

    all_outcome_weights = OutcomeWeight.objects.filter(
        component__in=components
    ).select_related("component", "outcome")
    comp_lo_weight_map = {
        (w.component_id, w.outcome_id): w.weight for w in all_outcome_weights
    }

    student_lo_scores = []
    for student in students:
        student_lo_data = []
        for outcome in outcomes:
            lo_weighted_score = Decimal("0.0")
            lo_total_weight = Decimal("0.0")

            for component in components:
                grade_score = grade_map.get((student.id, component.id))
                if grade_score is None:
                    continue

                comp_lo_weight = comp_lo_weight_map.get((component.id, outcome.id))
                if not comp_lo_weight:
                    continue

                comp_weight_to_lo = Decimal(comp_lo_weight)
                lo_weighted_score += Decimal(grade_score) * comp_weight_to_lo
                lo_total_weight += comp_weight_to_lo

            if lo_total_weight > 0:
                lo_score = lo_weighted_score / lo_total_weight
                student_lo_data.append(
                    {
                        "outcome": outcome,
                        "score": float(lo_score.quantize(Decimal("0.01"))),
                    }
                )
            else:
                student_lo_data.append(
                    {
                        "outcome": outcome,
                        "score": None,
                    }
                )

        student_lo_scores.append(
            {
                "student": student,
                "lo_scores": student_lo_data,
            }
        )

    context = {
        "course": course,
        "components": components,
        "outcomes": outcomes,
        "students": students,
        "student_grade_rows": student_grade_rows,
        "student_lo_scores": student_lo_scores,
        "eval_form": eval_form,
        "outcome_form": outcome_form,
        "syllabus_form": syllabus_form,
    }

    return render(
        request,
        "teacher/course_manage_detail.html",
        context,
    )


@login_required
@user_is_instructor
def add_learning_outcome(request, course_id):
    course = get_object_or_404(Course, id=course_id, instructors=request.user)

    if request.method == "POST":
        form = LearningOutcomeForm(request.POST)
        if form.is_valid():
            lo = form.save(commit=False)
            lo.course = course
            lo.save()
            messages.success(request, "Öğrenim çıktısı başarıyla eklendi.")
            return redirect("instructor_dashboard")
    else:
        form = LearningOutcomeForm()

    context = {
        "course": course,
        "form": form,
    }
    return render(request, "teacher/add_learning_outcome.html", context)


@login_required
@user_is_instructor
def add_evaluation_component(request, course_id):
    course = get_object_or_404(Course, id=course_id, instructors=request.user)

    if request.method == "POST":
        form = EvaluationComponentForm(request.POST)
        if form.is_valid():
            comp = form.save(commit=False)
            comp.course = course
            comp.save()
            messages.success(request, "Değerlendirme bileşeni başarıyla eklendi.")
            return redirect("instructor_dashboard")
    else:
        form = EvaluationComponentForm()

    context = {
        "course": course,
        "form": form,
    }
    return render(request, "teacher/add_evaluation_component.html", context)


@login_required
@user_is_instructor
def manage_outcome_weights(request, component_id):
    component = get_object_or_404(
        EvaluationComponent,
        id=component_id,
        course__instructors=request.user,
    )
    course = component.course
    outcomes = course.learning_outcomes.all()

    if request.method == "POST":
        for outcome in outcomes:
            field_name = f"weight_{outcome.id}"
            value = request.POST.get(field_name)

            if value:
                value_int = int(value)
                OutcomeWeight.objects.update_or_create(
                    component=component,
                    outcome=outcome,
                    defaults={"weight": value_int},
                )
            else:
                OutcomeWeight.objects.filter(
                    component=component,
                    outcome=outcome,
                ).delete()

        messages.success(request, "Outcome ağırlıkları başarıyla güncellendi.")
        return redirect("instructor_dashboard")

    existing_weights = OutcomeWeight.objects.filter(component=component)
    weight_map = {w.outcome_id: w.weight for w in existing_weights}

    rows = []
    for outcome in outcomes:
        rows.append(
            {
                "outcome": outcome,
                "weight": weight_map.get(outcome.id),
            }
        )

    context = {
        "component": component,
        "course": course,
        "rows": rows,
    }
    return render(request, "teacher/manage_outcome_weights.html", context)


@login_required
@user_is_instructor
def add_grade(request, component_id):
    component = get_object_or_404(
        EvaluationComponent,
        id=component_id,
        course__instructors=request.user,
    )
    course = component.course

    if request.method == "POST":
        form = GradeForm(request.POST, course=course)
        if form.is_valid():
            student = form.cleaned_data["student"]
            score = form.cleaned_data["score"]

            grade, created = Grade.objects.get_or_create(
                student=student,
                component=component,
                defaults={"score": score},
            )

            if not created:
                grade.score = score
            grade.save()

            messages.success(request, "Öğrenci notu başarıyla kaydedildi.")
            return redirect("instructor_dashboard")
    else:
        form = GradeForm(course=course)

    context = {
        "component": component,
        "course": course,
        "form": form,
    }
    return render(request, "teacher/add_grade.html", context)


@login_required
@user_is_instructor
def instructor_manage_component_outcomes(request, course_id=None):
    if course_id:
        courses = Course.objects.filter(
            id=course_id,
            instructors=request.user,
        ).prefetch_related("evaluation_components", "learning_outcomes")
    else:
        courses = Course.objects.filter(
            instructors=request.user,
        ).prefetch_related("evaluation_components", "learning_outcomes")

    course_data = []
    for course in courses:
        components = course.evaluation_components.all()
        outcomes = course.learning_outcomes.all()

        component_data = []
        for component in components:
            existing_weights = OutcomeWeight.objects.filter(component=component)
            weight_map = {w.outcome_id: w.weight for w in existing_weights}

            outcome_rows = []
            for outcome in outcomes:
                outcome_rows.append(
                    {
                        "outcome": outcome,
                        "weight": weight_map.get(outcome.id),
                    }
                )

            component_data.append(
                {
                    "component": component,
                    "outcome_rows": outcome_rows,
                }
            )

        course_data.append(
            {
                "course": course,
                "component_data": component_data,
                "outcomes": outcomes,
            }
        )

    if request.method == "POST":
        component_id = request.POST.get("component_id")
        component = get_object_or_404(
            EvaluationComponent,
            id=component_id,
            course__instructors=request.user,
        )
        course = component.course
        if not course_id:
            course_id = course.id
        outcomes = course.learning_outcomes.all()

        for outcome in outcomes:
            field_name = f"weight_{component_id}_{outcome.id}"
            value = request.POST.get(field_name)

            if value:
                value_int = int(value)
                OutcomeWeight.objects.update_or_create(
                    component=component,
                    outcome=outcome,
                    defaults={"weight": value_int},
                )
            else:
                OutcomeWeight.objects.filter(
                    component=component,
                    outcome=outcome,
                ).delete()

        messages.success(request, "Ağırlıklar başarıyla güncellendi.")
        if course_id:
            return redirect(
                "instructor_manage_course_component_outcomes",
                course_id=course_id,
            )
        return redirect("instructor_manage_component_outcomes")

    context = {
        "course_data": course_data,
    }
    return render(request, "teacher/instructor_manage_component_outcomes.html", context)


