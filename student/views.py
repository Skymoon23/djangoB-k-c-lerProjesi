from decimal import Decimal
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from course_management.decorators import user_is_student
from course_management.models import (
    Course, EvaluationComponent, Grade, LearningOutcomeProgramOutcomeWeight,
    OutcomeWeight, ProgramOutcome,
)

@login_required
@user_is_student
def student_dashboard(request):
    """Öğrencinin tüm derslerini ve notlarını gösterir."""
    enrolled_courses = request.user.enrolled_courses.all()
    course_data = []

    for course in enrolled_courses:
        components = EvaluationComponent.objects.filter(course=course).order_by("id")
        grades = Grade.objects.filter(student=request.user, component__in=components)
        outcomes = course.learning_outcomes.all()
        grade_map = {g.component_id: g.score for g in grades if g.score is not None}

        # Bileşen not listesi ve toplam skor hesaplama
        component_grade_list = [{"name": c.name, "percentage": c.percentage, "score": grade_map.get(c.id)} for c in components]
        total_score = sum(Decimal(grade_map.get(c.id, 0)) * (Decimal(c.percentage) / Decimal("100.0")) for c in components if grade_map.get(c.id) is not None)

        # Learning outcome skorlarını hesaplar
        comp_lo_weight_map = {(w.component_id, w.outcome_id): w.weight for w in OutcomeWeight.objects.filter(component__in=components).select_related("component", "outcome")}
        learning_outcome_scores = []

        for outcome in outcomes:
            lo_weighted_score = Decimal("0.0")
            lo_total_weight = Decimal("0.0")

            for component in components:
                grade_score = grade_map.get(component.id)
                if grade_score is None:
                    continue

                comp_lo_weight = comp_lo_weight_map.get((component.id, outcome.id))
                if not comp_lo_weight:
                    continue

                comp_weight_to_lo = Decimal(comp_lo_weight)
                lo_weighted_score += Decimal(grade_score) * comp_weight_to_lo
                lo_total_weight += comp_weight_to_lo

            learning_outcome_scores.append({
                "outcome": outcome,
                "score": float((lo_weighted_score / lo_total_weight).quantize(Decimal("0.01"))) if lo_total_weight > 0 else None
            })

        course_data.append({
            "course": course,
            "component_grade_list": component_grade_list,
            "final_grade": total_score.quantize(Decimal("0.01")),
            "learning_outcome_scores": learning_outcome_scores,
        })
    
    return render(request, "student/student_dashboard.html", {
        "course_data": course_data,
        "all_program_outcomes": ProgramOutcome.objects.all(),
    })


@login_required
@user_is_student
def student_course_detail(request, course_id):
    """Öğrencinin belirli bir derse ait detaylı not ve çıktı bilgilerini gösterir."""
    course = get_object_or_404(Course, id=course_id, students=request.user)
    components = EvaluationComponent.objects.filter(course=course)
    grades = Grade.objects.filter(student=request.user, component__in=components)
    outcomes = course.learning_outcomes.all()
    grade_map = {g.component_id: g.score for g in grades}

    # Bileşen not listesi
    component_grade_list = [{"name": c.name, "percentage": c.percentage, "score": grade_map.get(c.id)} for c in components]

    # Learning outcome skorlarını hesaplar
    comp_lo_weight_map = {(w.component_id, w.outcome_id): w.weight for w in OutcomeWeight.objects.filter(component__in=components).select_related("component", "outcome")}
    learning_outcome_scores = []
    learning_outcome_score_map = {}

    for outcome in outcomes:
        lo_weighted_score = Decimal("0.0")
        lo_total_weight = Decimal("0.0")

        for component in components:
            grade_score = grade_map.get(component.id)
            if grade_score is None:
                continue

            comp_lo_weight = comp_lo_weight_map.get((component.id, outcome.id))
            if not comp_lo_weight:
                continue

            comp_weight_to_lo = Decimal(comp_lo_weight)
            lo_weighted_score += Decimal(grade_score) * comp_weight_to_lo
            lo_total_weight += comp_weight_to_lo

        if lo_total_weight > 0:
            lo_score = (lo_weighted_score / lo_total_weight).quantize(Decimal("0.01"))
            learning_outcome_score_map[outcome.id] = lo_score
            learning_outcome_scores.append({"outcome": outcome, "score": float(lo_score)})
        else:
            learning_outcome_scores.append({"outcome": outcome, "score": None})

    # Program outcome skorlarını hesaplar
    lo_po_weights = LearningOutcomeProgramOutcomeWeight.objects.filter(learning_outcome__in=outcomes).select_related("program_outcome")
    po_score_map = {}

    for weight_obj in lo_po_weights:
        lo_score = learning_outcome_score_map.get(weight_obj.learning_outcome_id)
        if lo_score is None:
            continue

        po_entry = po_score_map.setdefault(weight_obj.program_outcome_id, {
            "program_outcome": weight_obj.program_outcome,
            "weighted_sum": Decimal("0.0"),
            "total_weight": Decimal("0.0"),
        })
        weight_decimal = Decimal(weight_obj.weight)
        po_entry["weighted_sum"] += lo_score * weight_decimal
        po_entry["total_weight"] += weight_decimal

    program_outcome_scores = [{
        "program_outcome": entry["program_outcome"],
        "score": float((entry["weighted_sum"] / entry["total_weight"]).quantize(Decimal("0.01"))) if entry["total_weight"] > 0 else None
    } for entry in po_score_map.values()]
    
    return render(request, "student/student_course_detail.html", {
        "course": course,
        "component_grade_list": component_grade_list,
        "learning_outcome_scores": learning_outcome_scores,
        "program_outcome_scores": program_outcome_scores,
    })
