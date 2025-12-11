from decimal import Decimal
import json
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from course_management.decorators import user_is_department_head
from course_management.forms import (
    CourseCreateForm, InstructorAssignForm, ProgramOutcomeForm, StudentAssignForm,
)
from course_management.models import (
    Course, Grade, LearningOutcome, LearningOutcomeProgramOutcomeWeight,
    OutcomeWeight, ProgramOutcome, User,
)


@login_required
@user_is_department_head
def department_head_dashboard(request):
    """Bölüm başkanının ana paneli - çoklu form işlemleri."""
    # Formları başlat
    course_form = CourseCreateForm()
    assign_form = InstructorAssignForm()
    student_assign_form = StudentAssignForm()
    program_outcome_form = ProgramOutcomeForm()

    # POST işlemleri
    if request.method == "POST":
        # ---------- 1) Yeni Ders Oluşturma ----------
        if "submit_course_create" in request.POST:
            course_form = CourseCreateForm(request.POST)
            if course_form.is_valid():
                course_form.save()
                messages.success(request, "Yeni ders başarıyla eklendi.")
                return redirect("department_head_dashboard")

            messages.error(request, "Ders eklenirken bir hata oluştu. Lütfen formu kontrol edin.")

        # ---------- 2) Hoca Atama ----------
        elif "submit_instructor_assign" in request.POST:
            assign_form = InstructorAssignForm(request.POST)
            if assign_form.is_valid():
                course = assign_form.cleaned_data["course"]
                instructor = assign_form.cleaned_data["instructor"]
                course.instructors.add(instructor)

                messages.success(
                    request,
                    f'"{instructor.get_full_name()}" hocası "{course.course_code}" dersine başarıyla atandı.'
                )
                return redirect("department_head_dashboard")

            messages.error(request, "Hoca atanırken bir hata oluştu. Lütfen formu kontrol edin.")

        # ---------- 3) Öğrenci Atama (Çoklu Checkbox Destekli) ----------
        elif "submit_student_assign" in request.POST:
            student_assign_form = StudentAssignForm(request.POST)
            if student_assign_form.is_valid():
                course = student_assign_form.cleaned_data["course"]
                students = student_assign_form.cleaned_data["students"]  # çoklu seçim

                for student in students:
                    course.students.add(student)

                messages.success(
                    request,
                    f"Seçilen öğrenciler '{course.course_code}' dersine başarıyla atandı."
                )
                return redirect("department_head_dashboard")

            messages.error(request, "Öğrenciler atanırken bir hata oluştu. Lütfen formu kontrol edin.")

        # ---------- 4) Program Çıktısı Ekleme ----------
        elif "submit_program_outcome" in request.POST:
            program_outcome_form = ProgramOutcomeForm(request.POST)
            if program_outcome_form.is_valid():
                program_outcome_form.save()
                messages.success(request, "Yeni program çıktısı başarıyla eklendi.")
                return redirect("department_head_dashboard")

            messages.error(request, "Program çıktısı eklenirken bir hata oluştu.")

    # Sistem verilerini alır
    all_courses = Course.objects.all().prefetch_related("instructors").order_by("course_code")
    all_instructors = User.objects.filter(profile__role="instructor").order_by("last_name", "first_name")
    all_students = User.objects.filter(profile__role="student").prefetch_related("enrolled_courses").order_by(
        "last_name", "first_name")
    all_program_outcomes = ProgramOutcome.objects.all()

    return render(request, "headteacher/department_head_dashboard.html", {
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
    })


@login_required
@user_is_department_head
def department_head_manage_lo_po_weights(request):
    """Learning Outcome - Program Outcome ağırlıklarını yönetir."""
    all_courses = Course.objects.all().prefetch_related("learning_outcomes")
    all_program_outcomes = ProgramOutcome.objects.all().order_by("code")

    # Ders verilerini hazırlar
    course_data = []

    for course in all_courses:
        outcomes = course.learning_outcomes.all()
        outcome_data = []

        for outcome in outcomes:
            weight_map = {w.program_outcome_id: w.weight for w in LearningOutcomeProgramOutcomeWeight.objects.filter(learning_outcome=outcome)}
            outcome_data.append({
                "outcome": outcome,
                "po_rows": [{"program_outcome": po, "weight": weight_map.get(po.id)} for po in all_program_outcomes],
            })

        course_data.append({"course": course, "outcome_data": outcome_data})

    # POST işlemi: Ağırlıkları günceller
    if request.method == "POST":
        outcome = get_object_or_404(LearningOutcome, id=request.POST.get("outcome_id"))

        for po in all_program_outcomes:
            value = request.POST.get(f"weight_{outcome.id}_{po.id}")
            if value:
                LearningOutcomeProgramOutcomeWeight.objects.update_or_create(learning_outcome=outcome, program_outcome=po, defaults={"weight": int(value)})
            else:
                LearningOutcomeProgramOutcomeWeight.objects.filter(learning_outcome=outcome, program_outcome=po).delete()

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': 'Ağırlıklar başarıyla güncellendi.'})

        messages.success(request, "Ağırlıklar başarıyla güncellendi.")
        return redirect("department_head_manage_lo_po_weights")

    return render(request, "headteacher/department_head_manage_lo_po_weights.html", {
        "course_data": course_data, "all_program_outcomes": all_program_outcomes,
    })


@login_required
@user_is_department_head
def department_head_view_outcomes(request):
    """Tüm derslerin learning outcome ve program outcome ilişkilerini görüntüler."""
    all_courses = Course.objects.all().prefetch_related("learning_outcomes", "evaluation_components")
    all_program_outcomes = ProgramOutcome.objects.all().order_by("code")

    course_data = []

    for course in all_courses:
        components, outcomes = course.evaluation_components.all(), course.learning_outcomes.all()
        course_data.append({
            "course": course,
            "component_lo_data": [{"component": c, "weights": OutcomeWeight.objects.filter(component=c).select_related("outcome")} for c in components],
            "lo_po_data": [{"outcome": o, "weights": LearningOutcomeProgramOutcomeWeight.objects.filter(learning_outcome=o).select_related("program_outcome")} for o in outcomes],
        })
    
    return render(request, "headteacher/department_head_view_outcomes.html", {
        "course_data": course_data, "all_program_outcomes": all_program_outcomes,
    })


@login_required
@user_is_department_head
def department_head_program_outcome_achievement(request):
    """Program outcome'ların öğrenilme durumunu gösterir - istatistikler hesaplar."""
    all_courses = Course.objects.all().prefetch_related("learning_outcomes", "evaluation_components", "students")
    all_program_outcomes = ProgramOutcome.objects.all().order_by("code")
    all_students = User.objects.filter(profile__role="student").prefetch_related("enrolled_courses", "grades")

    # Not ve ağırlık map'leri oluştur
    grade_map = {(g.student_id, g.component_id): g.score for g in Grade.objects.select_related("student", "component").filter(student__profile__role="student", score__isnull=False)}
    comp_lo_weight_map = {(w.component_id, w.outcome_id): w.weight for w in OutcomeWeight.objects.select_related("component", "outcome").all()}
    lo_po_weight_map = {(w.learning_outcome_id, w.program_outcome_id): w.weight for w in LearningOutcomeProgramOutcomeWeight.objects.select_related("learning_outcome", "program_outcome").all()}

    # Program outcome başarı skorlarını hesaplar
    po_achievement_data = []

    for po in all_program_outcomes:
        student_po_scores = []

        for student in all_students:
            student_po_score, student_po_weight = Decimal("0.0"), Decimal("0.0")

            for course in all_courses:
                if student not in course.students.all():
                    continue

                components, outcomes = list(course.evaluation_components.all()), list(course.learning_outcomes.all())

                for outcome in outcomes:
                    lo_po_weight = lo_po_weight_map.get((outcome.id, po.id))
                    if not lo_po_weight:
                        continue

                    lo_weight_to_po = Decimal(lo_po_weight)
                    lo_weighted_score = sum(Decimal(grade_map.get((student.id, c.id), 0)) * Decimal(comp_lo_weight_map.get((c.id, outcome.id), 0)) for c in components if grade_map.get((student.id, c.id)) and comp_lo_weight_map.get((c.id, outcome.id)))
                    lo_total_weight = sum(Decimal(comp_lo_weight_map.get((c.id, outcome.id), 0)) for c in components if comp_lo_weight_map.get((c.id, outcome.id)))

                    if lo_total_weight > 0:
                        lo_score = lo_weighted_score / lo_total_weight
                        student_po_score += lo_score * lo_weight_to_po
                        student_po_weight += lo_weight_to_po

            if student_po_weight > 0:
                student_po_scores.append(float(student_po_score / student_po_weight))

        po_achievement_data.append({
            "program_outcome": po,
            "average_score": sum(student_po_scores) / len(student_po_scores) if student_po_scores else 0,
            "min_score": min(student_po_scores) if student_po_scores else 0,
            "max_score": max(student_po_scores) if student_po_scores else 0,
            "student_count": len(student_po_scores),
        })
    
    return render(request, "headteacher/department_head_program_outcome_achievement.html", {
        "po_achievement_data": po_achievement_data,
    })


@login_required
@user_is_department_head
def delete_program_outcome(request, outcome_id):
    """Program outcome silme işlemi."""
    program_outcome = get_object_or_404(ProgramOutcome, id=outcome_id)

    if request.method == "POST":
        program_outcome.delete()
        messages.success(request, f'"{program_outcome.code}" program outcome\'ı başarıyla silindi.')
    else:
        messages.error(request, "Program outcome silme isteği başarısız oldu.")

    return redirect("department_head_dashboard")


@login_required
@user_is_department_head
def edit_program_outcome(request, outcome_id):
    """Program outcome düzenleme sayfası."""
    program_outcome = get_object_or_404(ProgramOutcome, id=outcome_id)

    if request.method == "POST":
        form = ProgramOutcomeForm(request.POST, instance=program_outcome)
        if form.is_valid():
            form.save()
            messages.success(request, f'"{program_outcome.code}" program outcome\'ı güncellendi.')
            return redirect("department_head_dashboard")

        messages.error(request, "Program outcome güncellenirken bir hata oluştu. Lütfen formu kontrol edin.")
    else:
        form = ProgramOutcomeForm(instance=program_outcome)

    return render(request, "headteacher/edit_program_outcome.html", {"form": form, "program_outcome": program_outcome})
