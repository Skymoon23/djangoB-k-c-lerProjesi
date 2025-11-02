from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from decimal import Decimal

# modeller
from .models import Profile, Course, EvaluationComponent, LearningOutcome, Grade

# formlarımız
from .forms import EvaluationComponentForm, LearningOutcomeForm

# decoratorlarımız <-- roller ile kontrol
from .decorators import user_is_instructor, user_is_student


@login_required
def dashboard_redirect(request):
    """
    kullanıcıyı giriş yaptıktan sonra rolüne göre
    doğru dashboard'a yönlendir
    """
    try:
        role = request.user.profile.role
    except Profile.DoesNotExist:
        if request.user.is_superuser:
            return redirect('admin:index')
        else:
            return redirect('login')

    if role == 'instructor':
        return redirect('instructor_dashboard')
    elif role == 'student':
        return redirect('student_dashboard')
    elif role == 'department_head':
        return redirect('admin:index')
    else:
        return redirect('login')


@login_required
@user_is_instructor
def instructor_dashboard(request):
    """
    giriş yapan hocanın derslerim sayfasını gösterir
    """
    courses = Course.objects.filter(instructors=request.user)
    context = {'courses': courses}
    return render(request, 'course_management/instructor_dashboard.html', context)


@login_required
@user_is_instructor
def manage_course(request, course_id):
    """
    hocanın ders yönettiği sayfa
    """

    course = get_object_or_404(Course, id=course_id, instructors=request.user)
    components = EvaluationComponent.objects.filter(course=course).order_by('id')
    outcomes = LearningOutcome.objects.filter(course=course)
    students = course.students.all().order_by('last_name', 'first_name')

    # POST işlemleri
    if request.method == 'POST':
        if 'submit_evaluation' in request.POST:
            eval_form = EvaluationComponentForm(request.POST)
            if eval_form.is_valid():
                evaluation = eval_form.save(commit=False)
                evaluation.course = course
                evaluation.save()
                return redirect('manage_course', course_id=course.id)

        elif 'submit_outcome' in request.POST:
            outcome_form = LearningOutcomeForm(request.POST)
            if outcome_form.is_valid():
                outcome = outcome_form.save(commit=False)
                outcome.course = course
                outcome.save()
                return redirect('manage_course', course_id=course.id)

        elif 'submit_grades' in request.POST:
            for key, value in request.POST.items():
                if key.startswith('grade_'):
                    try:
                        _, student_id, component_id = key.split('_')
                        score = value
                        grade, created = Grade.objects.get_or_create(
                            student_id=student_id,
                            component_id=component_id
                        )
                        grade.score = score if score else None
                        grade.save()
                    except (ValueError, Exception):
                        pass  # Hatalı girişi yoksay
            return redirect('manage_course', course_id=course.id)

    # GET işlemi
    eval_form = EvaluationComponentForm()
    outcome_form = LearningOutcomeForm()

    # tüm notları tek seferde çekme
    all_grades = Grade.objects.filter(component__in=components, student__in=students)
    grade_map = {
        (g.student_id, g.component_id): g.score
        for g in all_grades
    }

    # template de döngüye sokma
    student_grade_rows = []
    for student in students:
        row = {
            'student_object': student,
            'grades_list': []
        }
        for component in components:
            # notu mapten al yoksa None
            score = grade_map.get((student.id, component.id))
            row['grades_list'].append({
                'component_id': component.id,
                'score': score
            })
        student_grade_rows.append(row)

    context = {
        'course': course,
        'components': components,  # başlık
        'outcomes': outcomes,
        'eval_form': eval_form,
        'outcome_form': outcome_form,
        'students': students,  # öğrenci sayısını kontrol için
        'student_grade_rows': student_grade_rows,  # not tablosu için
    }
    return render(request, 'course_management/course_manage_detail.html', context)


@login_required
@user_is_student
def student_dashboard(request):
    """
    giriş yapan öğrencinin notlarım sayfasını gösterir
    """
    enrolled_courses = request.user.enrolled_courses.all()
    course_data = []

    for course in enrolled_courses:
        components = EvaluationComponent.objects.filter(course=course).order_by('id')
        grades = Grade.objects.filter(student=request.user, component__in=components)

        total_score = Decimal('0.0')

        # notları eşleştir
        grade_map = {g.component_id: g.score for g in grades if g.score is not None}

        # veriyi template için hazırlama
        component_grade_list = []
        for comp in components:
            score = grade_map.get(comp.id)
            component_grade_list.append({
                'name': comp.name,
                'percentage': comp.percentage,
                'score': score  # not yoksa None
            })

            if score is not None:
                total_score += (score * (Decimal(comp.percentage) / Decimal('100.0')))

        course_data.append({
            'course': course,
            'component_grade_list': component_grade_list,
            'final_grade': total_score.quantize(Decimal('0.01')),
        })

    context = {
        'course_data': course_data,
    }
    return render(request, 'course_management/student_dashboard.html', context)
