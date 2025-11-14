from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from decimal import Decimal
from django.contrib import messages

# modeller
from .models import Profile, Course, EvaluationComponent, LearningOutcome, OutcomeWeight, Grade, User, ProgramOutcome

# formlar
from .forms import EvaluationComponentForm, GradeForm,  LearningOutcomeForm, CourseCreateForm, InstructorAssignForm, StudentAssignForm, SyllabusForm, ProgramOutcomeForm

# decoratorlarımız <-- roller ile kontrol
from .decorators import user_is_instructor, user_is_student, user_is_department_head

def home(request):
    return render(request, 'registration/home.html')



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
        return redirect('department_head_dashboard')
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
    hocanın ders yönettiği sayfa (ÇOKLU FORM YÖNETİMİ İÇİN GÜNCELLENDİ)
    """
    course = get_object_or_404(Course, id=course_id, instructors=request.user)
    components = EvaluationComponent.objects.filter(course=course).order_by('id')
    outcomes = LearningOutcome.objects.filter(course=course)
    students = course.students.all().order_by('last_name', 'first_name')

    # instance=course -> mevcut syllabusu göstermek için
    syllabus_form = SyllabusForm(instance=course)
    eval_form = EvaluationComponentForm()
    outcome_form = LearningOutcomeForm()

    # POST işlemleri
    if request.method == 'POST':

        # hangi formun gönderildiğini name ile kontrol et

        if 'submit_evaluation' in request.POST:
            eval_form = EvaluationComponentForm(request.POST)
            if eval_form.is_valid():
                evaluation = eval_form.save(commit=False)
                evaluation.course = course
                evaluation.save()
                messages.success(request, 'Değerlendirme bileşeni başarıyla eklendi.')
                return redirect('manage_course', course_id=course.id)
            # hata varsa sayfa yeniden render edilecek (en altta)
            # ve eval_form hataları gösterecek

        elif 'submit_outcome' in request.POST:
            # sadece gönderilen formu doldur
            outcome_form = LearningOutcomeForm(request.POST)
            if outcome_form.is_valid():
                outcome = outcome_form.save(commit=False)
                outcome.course = course
                outcome.save()
                messages.success(request, 'Öğrenim çıktısı başarıyla eklendi.')
                return redirect('manage_course', course_id=course.id)
            # hata varsa sayfa outcome_form ile render edilecek

        elif 'submit_syllabus' in request.POST:
            # sadece gönderilen formu dosya dahil yeniden doldur
            syllabus_form = SyllabusForm(request.POST, request.FILES, instance=course)
            if syllabus_form.is_valid():
                syllabus_form.save()
                messages.success(request, 'Syllabus dosyası başarıyla güncellendi.')
                return redirect('manage_course', course_id=course.id)
            else:
                # dosya geçersizse örneğin dosya seçilmedi ya da yanlış format
                # hata mesajı ver ve sayfayı syllabus_form un hatalarıyla render et
                messages.error(request, 'Dosya yüklenirken bir hata oluştu. Lütfen geçerli bir dosya seçin.')

        elif 'submit_grades' in request.POST:
            try:
                for key, value in request.POST.items():
                    if key.startswith('grade_'):
                        _, student_id, component_id = key.split('_')
                        score = value
                        grade, created = Grade.objects.get_or_create(
                            student_id=student_id,
                            component_id=component_id
                        )
                        grade.score = score if score else None
                        grade.save()
                messages.success(request, 'Notlar başarıyla kaydedildi.')
            except (ValueError, Exception) as e:
                messages.error(request, f'Notları kaydederken bir hata oluştu: {e}')
                pass  # hata olsa bile sayfayı yenile
            return redirect('manage_course', course_id=course.id)

    # GET İşlemleri veya POST'ta hata olduysa sayfanın yeniden render edilmesi

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
            score = grade_map.get((student.id, component.id))
            row['grades_list'].append({
                'component_id': component.id,
                'score': score
            })
        student_grade_rows.append(row)

    context = {
        'course': course,
        'components': components,
        'outcomes': outcomes,
        'students': students,
        'student_grade_rows': student_grade_rows,

        # formları hata varsa hatalı yoksa boş olarak context e yolla
        'eval_form': eval_form,
        'outcome_form': outcome_form,
        'syllabus_form': syllabus_form,
    }

    # Bu render GET isteği için VEYA
    # POST ta validasyon hatası olursa veya redirect olmazsa çalışır.
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

    all_program_outcomes = ProgramOutcome.objects.all()

    context = {
        'course_data': course_data,
        'all_program_outcomes': all_program_outcomes,
    }
    return render(request, 'course_management/student_dashboard.html', context)


@login_required
@user_is_department_head
def department_head_dashboard(request):
    """
    bölüm başkanının panelini gösterir
    tüm dersler hocalar ve öğrenciler hakkında genel bilgi sağlar
    ders ekleme, hoca atama ve öğrenci atama işlemlerini de yapar
    """

    # formları POST verisiyle doldur (eğer POST ise) veya boş oluştur (eğer GET ise)
    if request.method == 'POST':
        # hangi formun gönderildiğini submit butonunun name ye göre kontrol et

        if 'submit_course_create' in request.POST:
            course_form = CourseCreateForm(request.POST)
            assign_form = InstructorAssignForm()  # diğer formu boş ata
            student_assign_form = StudentAssignForm()  # diğer formu boş ata

            if course_form.is_valid():
                course_form.save()
                messages.success(request, 'Yeni ders başarıyla eklendi.')
                return redirect('department_head_dashboard')
            else:
                messages.error(request, 'Ders eklenirken bir hata oluştu. Lütfen formu kontrol edin.')

        elif 'submit_instructor_assign' in request.POST:
            assign_form = InstructorAssignForm(request.POST)
            course_form = CourseCreateForm()  # diğer formu boş ata
            student_assign_form = StudentAssignForm()  # diğer formu boş ata

            if assign_form.is_valid():
                course = assign_form.cleaned_data['course']
                instructor = assign_form.cleaned_data['instructor']

                # ManyToMany alanına hocayı ekle
                course.instructors.add(instructor)

                messages.success(request,
                                 f'"{instructor.get_full_name()}" hocası "{course.course_code}" dersine başarıyla atandı.')
                return redirect('department_head_dashboard')
            else:
                messages.error(request, 'Hoca atanırken bir hata oluştu. Lütfen formu kontrol edin.')

        elif 'submit_student_assign' in request.POST:
            student_assign_form = StudentAssignForm(request.POST)
            course_form = CourseCreateForm()  # diğer formu boş ata
            assign_form = InstructorAssignForm()  # diğer formu boş ata

            if student_assign_form.is_valid():
                course = student_assign_form.cleaned_data['course']
                student = student_assign_form.cleaned_data['student']

                # ManyToMany alanına öğrenciyi ekle
                course.students.add(student)

                messages.success(request,
                                 f'"{student.get_full_name()}" öğrencisi "{course.course_code}" dersine başarıyla atandı.')
                return redirect('department_head_dashboard')
            else:
                messages.error(request, 'Öğrenci atanırken bir hata oluştu. Lütfen formu kontrol edin.')

        elif 'submit_program_outcome' in request.POST:
            program_outcome_form = ProgramOutcomeForm(request.POST)
            # diğer formları boş ata
            course_form = CourseCreateForm()
            assign_form = InstructorAssignForm()
            student_assign_form = StudentAssignForm()

            if program_outcome_form.is_valid():
                program_outcome_form.save()
                messages.success(request, 'Yeni program çıktısı başarıyla eklendi.')
                return redirect('department_head_dashboard')
            else:
                messages.error(request, 'Program çıktısı eklenirken bir hata oluştu.')

        else:
            # beklenmedik bir POST durumu
            course_form = CourseCreateForm()
            assign_form = InstructorAssignForm()
            student_assign_form = StudentAssignForm()
            program_outcome_form = ProgramOutcomeForm()

    else:
        # tüm formları boş olarak oluştur
        course_form = CourseCreateForm()
        assign_form = InstructorAssignForm()
        student_assign_form = StudentAssignForm()
        program_outcome_form = ProgramOutcomeForm()


    # instructors kullanarak veritabanı sorgusunu optimize et
    # ders listesinde hocaları gösterirken her ders için ayrı sorgu atmama
    all_courses = Course.objects.all().prefetch_related('instructors').order_by('course_code')

    all_instructors = User.objects.filter(profile__role='instructor').order_by('last_name', 'first_name')
    all_students = User.objects.filter(profile__role='student').prefetch_related('enrolled_courses').order_by('last_name', 'first_name')
    all_program_outcomes = ProgramOutcome.objects.all()

    context = {
        'all_courses': all_courses,
        'all_instructors': all_instructors,
        'all_students': all_students,
        'course_count': all_courses.count(),
        'instructor_count': all_instructors.count(),
        'student_count': all_students.count(),
        'course_form': course_form,
        'assign_form': assign_form,
        'student_assign_form': student_assign_form,
        'program_outcome_form': program_outcome_form,
        'all_program_outcomes': all_program_outcomes,
    }

    return render(request, 'course_management/department_head_dashboard.html', context)
























@login_required
@user_is_instructor
def add_learning_outcome(request, course_id):
    course = get_object_or_404(Course, id=course_id, instructors=request.user)

    if request.method == 'POST':
        form = LearningOutcomeForm(request.POST)
        if form.is_valid():
            lo = form.save(commit=False)
            lo.course = course   # formda course alanı yok, burada bağlıyoruz
            lo.save()
            messages.success(request, "Öğrenim çıktısı başarıyla eklendi.")
            return redirect('instructor_dashboard')
    else:
        form = LearningOutcomeForm()

    context = {
        'course': course,
        'form': form,
    }
    return render(request, 'course_management/add_learning_outcome.html', context)



@login_required
@user_is_instructor
def add_evaluation_component(request, course_id):
    course = get_object_or_404(Course, id=course_id, instructors=request.user)

    if request.method == 'POST':
        form = EvaluationComponentForm(request.POST)
        if form.is_valid():
            comp = form.save(commit=False)
            comp.course = course
            comp.save()
            messages.success(request, "Değerlendirme bileşeni başarıyla eklendi.")
            return redirect('instructor_dashboard')
    else:
        form = EvaluationComponentForm()

    context = {
        'course': course,
        'form': form,
    }
    return render(request, 'course_management/add_evaluation_component.html', context)


@login_required
@user_is_instructor
def manage_outcome_weights(request, component_id):
    component = get_object_or_404(
        EvaluationComponent,
        id=component_id,
        course__instructors=request.user
    )
    course = component.course
    outcomes = course.learning_outcomes.all()

    if request.method == 'POST':
        for outcome in outcomes:
            field_name = f"weight_{outcome.id}"
            value = request.POST.get(field_name)

            if value:
                value_int = int(value)
                # varsa güncelle, yoksa oluştur
                OutcomeWeight.objects.update_or_create(
                    component=component,
                    outcome=outcome,
                    defaults={'weight': value_int}
                )
            else:
                # hiç bir şey seçilmemişse kaydı silebilirsin (istersen)
                OutcomeWeight.objects.filter(
                    component=component,
                    outcome=outcome
                ).delete()

        messages.success(request, "Outcome ağırlıkları başarıyla güncellendi.")
        return redirect('instructor_dashboard')

    # GET isteği: mevcut ağırlıkları çek
    existing_weights = OutcomeWeight.objects.filter(component=component)
    weight_map = {w.outcome_id: w.weight for w in existing_weights}

    # Template'te kullanmak için her outcome + ağırlığı tek listede topla
    rows = []
    for outcome in outcomes:
        rows.append({
            "outcome": outcome,
            "weight": weight_map.get(outcome.id)  # yoksa None
        })

    context = {
        'component': component,
        'course': course,
        'rows': rows,     # 🔥 template buna göre çalışacak
    }
    return render(request, 'course_management/manage_outcome_weights.html', context)



@login_required
@user_is_instructor
def add_grade(request, component_id):
    component = get_object_or_404(
        EvaluationComponent,
        id=component_id,
        course__instructors=request.user
    )
    course = component.course

    if request.method == 'POST':
        form = GradeForm(request.POST, course=course)
        if form.is_valid():
            grade = form.save(commit=False)
            grade.component = component  # Hangi bileşenin notu olduğu
            grade.save()
            messages.success(request, "Öğrenci notu başarıyla kaydedildi.")
            return redirect('instructor_dashboard')
    else:
        form = GradeForm(course=course)

    context = {
        'component': component,
        'course': course,
        'form': form,
    }
    return render(request, 'course_management/add_grade.html', context)


@login_required
@user_is_student
def student_course_detail(request, course_id):
    course = get_object_or_404(Course, id=course_id, students=request.user)

    components = EvaluationComponent.objects.filter(course=course)
    grades = Grade.objects.filter(student=request.user, component__in=components)

    grade_map = {g.component_id: g.score for g in grades}

    component_grade_list = []
    for comp in components:
        component_grade_list.append({
            "name": comp.name,
            "percentage": comp.percentage,
            "score": grade_map.get(comp.id)
        })

    context = {
        "course": course,
        "component_grade_list": component_grade_list,
    }

    return render(request, "course_management/student_course_detail.html", context)
