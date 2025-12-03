from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render

from course_management.decorators import user_is_student
from course_management.models import (
    Course,
    EvaluationComponent,
    Grade,
    LearningOutcomeProgramOutcomeWeight,
    OutcomeWeight,
    ProgramOutcome,
)


@login_required
@user_is_student
def student_dashboard(request):
    """
    Giriş yapan öğrencinin notlarım sayfasını gösterir.
    Önceki implementasyon course_management.views içinden taşındı.
    """
    enrolled_courses = request.user.enrolled_courses.all()
    course_data = []

    for course in enrolled_courses:
        components = EvaluationComponent.objects.filter(course=course).order_by("id")
        grades = Grade.objects.filter(student=request.user, component__in=components)
        outcomes = course.learning_outcomes.all()

        total_score = Decimal("0.0")

        grade_map = {g.component_id: g.score for g in grades if g.score is not None}

        component_grade_list = []
        for comp in components:
            score = grade_map.get(comp.id)
            component_grade_list.append(
                {
                    "name": comp.name,
                    "percentage": comp.percentage,
                    "score": score,
                }
            )

            if score is not None:
                total_score += score * (Decimal(comp.percentage) / Decimal("100.0"))

        all_outcome_weights = OutcomeWeight.objects.filter(
            component__in=components
        ).select_related("component", "outcome")
        comp_lo_weight_map = {
            (w.component_id, w.outcome_id): w.weight for w in all_outcome_weights
        }

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

            if lo_total_weight > 0:
                lo_score = lo_weighted_score / lo_total_weight
                learning_outcome_scores.append(
                    {
                        "outcome": outcome,
                        "score": float(lo_score.quantize(Decimal("0.01"))),
                    }
                )
            else:
                learning_outcome_scores.append(
                    {
                        "outcome": outcome,
                        "score": None,
                    }
                )

        course_data.append(
            {
                "course": course,
                "component_grade_list": component_grade_list,
                "final_grade": total_score.quantize(Decimal("0.01")),
                "learning_outcome_scores": learning_outcome_scores,
            }
        )

    all_program_outcomes = ProgramOutcome.objects.all()

    context = {
        "course_data": course_data,
        "all_program_outcomes": all_program_outcomes,
    }
    return render(request, "student/student_dashboard.html", context)


@login_required
@user_is_student
def student_course_detail(request, course_id):
    """
    Öğrencinin belirli bir derse ait not ve çıktı detaylarını gösterir.
    Önceki implementasyon course_management.views içinden taşındı.
    """
    course = get_object_or_404(Course, id=course_id, students=request.user)

    components = EvaluationComponent.objects.filter(course=course)
    grades = Grade.objects.filter(student=request.user, component__in=components)
    outcomes = course.learning_outcomes.all()

    grade_map = {g.component_id: g.score for g in grades}

    component_grade_list = []
    for comp in components:
        component_grade_list.append(
            {
                "name": comp.name,
                "percentage": comp.percentage,
                "score": grade_map.get(comp.id),
            }
        )

    all_outcome_weights = OutcomeWeight.objects.filter(
        component__in=components
    ).select_related("component", "outcome")
    comp_lo_weight_map = {
        (w.component_id, w.outcome_id): w.weight for w in all_outcome_weights
    }

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
            lo_score = lo_weighted_score / lo_total_weight
            lo_score = lo_score.quantize(Decimal("0.01"))
            learning_outcome_score_map[outcome.id] = lo_score
            learning_outcome_scores.append(
                {
                    "outcome": outcome,
                    "score": float(lo_score),
                }
            )
        else:
            learning_outcome_scores.append(
                {
                    "outcome": outcome,
                    "score": None,
                }
            )

    lo_po_weights = LearningOutcomeProgramOutcomeWeight.objects.filter(
        learning_outcome__in=outcomes
    ).select_related("program_outcome")

    po_score_map = {}
    for weight_obj in lo_po_weights:
        lo_score = learning_outcome_score_map.get(weight_obj.learning_outcome_id)
        if lo_score is None:
            continue

        po_entry = po_score_map.setdefault(
            weight_obj.program_outcome_id,
            {
                "program_outcome": weight_obj.program_outcome,
                "weighted_sum": Decimal("0.0"),
                "total_weight": Decimal("0.0"),
            },
        )

        weight_decimal = Decimal(weight_obj.weight)
        po_entry["weighted_sum"] += lo_score * weight_decimal
        po_entry["total_weight"] += weight_decimal

    program_outcome_scores = []
    for entry in po_score_map.values():
        if entry["total_weight"] > 0:
            score = (
                entry["weighted_sum"] / entry["total_weight"]
            ).quantize(Decimal("0.01"))
            program_outcome_scores.append(
                {
                    "program_outcome": entry["program_outcome"],
                    "score": float(score),
                }
            )
        else:
            program_outcome_scores.append(
                {
                    "program_outcome": entry["program_outcome"],
                    "score": None,
                }
            )

    context = {
        "course": course,
        "component_grade_list": component_grade_list,
        "learning_outcome_scores": learning_outcome_scores,
        "program_outcome_scores": program_outcome_scores,
    }

    return render(
        request,
        "student/student_course_detail.html",
        context,
    )


