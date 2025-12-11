from decimal import Decimal, InvalidOperation
import json
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from course_management.decorators import user_is_instructor
from course_management.forms import (
    EvaluationComponentForm, GradeForm, LearningOutcomeForm, SyllabusForm,
)
from course_management.models import (
    Course, EvaluationComponent, Grade, LearningOutcome, OutcomeWeight,
)

@login_required
@user_is_instructor
def instructor_dashboard(request):
    """Öğretim görevlisinin derslerini listeler."""
    return render(request, "teacher/instructor_dashboard.html", {
        "courses": Course.objects.filter(instructors=request.user)
    })

@login_required
@user_is_instructor
def manage_course(request, course_id):
    """Öğretim görevlisinin ders yönetim sayfası - çoklu form işlemleri."""
    course = get_object_or_404(Course, id=course_id, instructors=request.user)
    components = EvaluationComponent.objects.filter(course=course).order_by("id")
    outcomes = LearningOutcome.objects.filter(course=course)
    students = course.students.all().order_by("last_name", "first_name")
    syllabus_form = SyllabusForm(instance=course)
    eval_form = EvaluationComponentForm()
    outcome_form = LearningOutcomeForm()

    # POST işlemleri
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
            syllabus_form = SyllabusForm(request.POST, request.FILES, instance=course)
            if syllabus_form.is_valid():
                syllabus_form.save()
                messages.success(request, "Syllabus dosyası başarıyla güncellendi.")
                return redirect("manage_course", course_id=course.id)
            else:
                messages.error(request, "Dosya yüklenirken bir hata oluştu. Lütfen geçerli bir dosya seçin.")


        elif "submit_grades" in request.POST:

            # form üzerinden gelen notları kaydet

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

                            if not (0 <= score_decimal <= 100):
                                continue

                        except (ValueError, InvalidOperation):

                            continue

                    else:

                        score_decimal = None

                    grade, _ = Grade.objects.get_or_create(student_id=student_id, component_id=component_id)

                    grade.score = score_decimal

                    grade.save()

                messages.success(request, "Notlar başarıyla kaydedildi.")


            except Exception as e:

                messages.error(request, f"Notları kaydederken bir hata oluştu: {e}")

            return redirect("manage_course", course_id=course.id)

        elif "submit_excel_grades" in request.POST:

            uploaded_file = request.FILES.get("grades_file")

            if not uploaded_file:
                messages.error(request, "Lütfen bir Excel dosyası yükleyin.")

                return redirect("manage_course", course_id=course.id)

            import openpyxl

            try:

                workbook = openpyxl.load_workbook(uploaded_file)

                sheet = workbook.active

                for row in sheet.iter_rows(min_row=2, values_only=True):

                    student_number, username, component_name, score = row

                    if not (student_number or username) or not component_name:
                        continue

                    student = None
                    if student_number:
                        student = course.students.filter(student_number=student_number).first()

                        if not student and username:
                            student = course.students.filter(username=username).first()

                    component = EvaluationComponent.objects.filter(course=course, name=component_name).first()

                    if student and component:
                        Grade.objects.update_or_create(

                            student=student,

                            component=component,

                            defaults={"score": score}

                        )

                messages.success(request, "Excel dosyasından notlar başarıyla yüklendi.")


            except Exception as e:

                messages.error(request, f"Excel işleme hatası: {e}")

            return redirect("manage_course", course_id=course.id)

    # Öğrenci notlarını hazırla
    grade_map = {(g.student_id, g.component_id): g.score for g in Grade.objects.filter(component__in=components, student__in=students)}
    student_grade_rows = [{
        "student_object": s,
        "grades_list": [{"component_id": c.id, "score": grade_map.get((s.id, c.id))} for c in components]
    } for s in students]

    # Learning outcome skorlarını hesapla
    comp_lo_weight_map = {(w.component_id, w.outcome_id): w.weight for w in OutcomeWeight.objects.filter(component__in=components).select_related("component", "outcome")}
    student_lo_scores = []

    for student in students:
        student_lo_data = []

        for outcome in outcomes:
            lo_weighted_score = sum(Decimal(grade_map.get((student.id, c.id), 0)) * Decimal(comp_lo_weight_map.get((c.id, outcome.id), 0)) for c in components if grade_map.get((student.id, c.id)) and comp_lo_weight_map.get((c.id, outcome.id)))
            lo_total_weight = sum(Decimal(comp_lo_weight_map.get((c.id, outcome.id), 0)) for c in components if comp_lo_weight_map.get((c.id, outcome.id)))
            student_lo_data.append({
                "outcome": outcome,
                "score": float((lo_weighted_score / lo_total_weight).quantize(Decimal("0.01"))) if lo_total_weight > 0 else None
            })

        student_lo_scores.append({"student": student, "lo_scores": student_lo_data})

    return render(request, "teacher/course_manage_detail.html", {
        "course": course, "components": components, "outcomes": outcomes, "students": students,
        "student_grade_rows": student_grade_rows, "student_lo_scores": student_lo_scores,
        "eval_form": eval_form, "outcome_form": outcome_form, "syllabus_form": syllabus_form,
    })


@login_required
@user_is_instructor
def add_learning_outcome(request, course_id):
    """Yeni learning outcome ekleme sayfası."""
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

    return render(request, "teacher/add_learning_outcome.html", {"course": course, "form": form})


@login_required
@user_is_instructor
def add_evaluation_component(request, course_id):
    """Yeni değerlendirme bileşeni (Vize, Final, vb.) ekleme sayfası."""
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

    return render(request, "teacher/add_evaluation_component.html", {"course": course, "form": form})


@login_required
@user_is_instructor
def manage_outcome_weights(request, component_id):
    """Bir değerlendirme bileşeninin learning outcome ağırlıklarını yönetir."""
    component = get_object_or_404(EvaluationComponent, id=component_id, course__instructors=request.user)
    course = component.course
    outcomes = course.learning_outcomes.all()

    if request.method == "POST":
        for outcome in outcomes:
            value = request.POST.get(f"weight_{outcome.id}")
            if value:
                OutcomeWeight.objects.update_or_create(component=component, outcome=outcome, defaults={"weight": int(value)})
            else:
                OutcomeWeight.objects.filter(component=component, outcome=outcome).delete()
        messages.success(request, "Outcome ağırlıkları başarıyla güncellendi.")
        return redirect("instructor_dashboard")

    weight_map = {w.outcome_id: w.weight for w in OutcomeWeight.objects.filter(component=component)}
    return render(request, "teacher/manage_outcome_weights.html", {
        "component": component, "course": course,
        "rows": [{"outcome": o, "weight": weight_map.get(o.id)} for o in outcomes],
    })


@login_required
@user_is_instructor
def add_grade(request, component_id):
    """Tek bir öğrenci için not ekleme/güncelleme sayfası."""
    component = get_object_or_404(EvaluationComponent, id=component_id, course__instructors=request.user)
    course = component.course

    if request.method == "POST":
        form = GradeForm(request.POST, course=course)
        if form.is_valid():
            student, score = form.cleaned_data["student"], form.cleaned_data["score"]
            grade, created = Grade.objects.get_or_create(student=student, component=component, defaults={"score": score})
            if not created:
                grade.score = score
            grade.save()
            messages.success(request, "Öğrenci notu başarıyla kaydedildi.")
            return redirect("instructor_dashboard")
    else:
        form = GradeForm(course=course)

    return render(request, "teacher/add_grade.html", {"component": component, "course": course, "form": form})


@login_required
@user_is_instructor
def instructor_manage_component_outcomes(request, course_id=None):
    """Tüm derslerin veya belirli bir dersin component-outcome ağırlıklarını yönetir."""
    courses = Course.objects.filter(id=course_id, instructors=request.user).prefetch_related("evaluation_components", "learning_outcomes") if course_id else Course.objects.filter(instructors=request.user).prefetch_related("evaluation_components", "learning_outcomes")

    course_data = []

    for course in courses:
        components, outcomes = course.evaluation_components.all(), course.learning_outcomes.all()
        component_data = []

        for component in components:
            weight_map = {w.outcome_id: w.weight for w in OutcomeWeight.objects.filter(component=component)}
            component_data.append({
                "component": component,
                "outcome_rows": [{"outcome": o, "weight": weight_map.get(o.id)} for o in outcomes],
            })

        course_data.append({"course": course, "component_data": component_data, "outcomes": outcomes})

    if request.method == "POST":
        component = get_object_or_404(EvaluationComponent, id=request.POST.get("component_id"), course__instructors=request.user)
        course = component.course
        if not course_id:
            course_id = course.id

        outcomes = course.learning_outcomes.all()

        for outcome in outcomes:
            value = request.POST.get(f"weight_{component.id}_{outcome.id}")
            if value:
                OutcomeWeight.objects.update_or_create(component=component, outcome=outcome, defaults={"weight": int(value)})
            else:
                OutcomeWeight.objects.filter(component=component, outcome=outcome).delete()

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': 'Ağırlıklar başarıyla güncellendi.'})

        messages.success(request, "Ağırlıklar başarıyla güncellendi.")
        return redirect("instructor_manage_course_component_outcomes", course_id=course_id) if course_id else redirect("instructor_manage_component_outcomes")

    return render(request, "teacher/instructor_manage_outcomes.html", {"course_data": course_data})
