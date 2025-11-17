from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from decimal import Decimal, InvalidOperation
from django.contrib import messages

# modeller
from .models import Profile, Course, EvaluationComponent, LearningOutcome, OutcomeWeight, Grade, User, ProgramOutcome, LearningOutcomeProgramOutcomeWeight

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
                        parts = key.split('_')
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
                        
                        grade, created = Grade.objects.get_or_create(
                            student_id=student_id,
                            component_id=component_id
                        )
                        grade.score = score_decimal
                        grade.save()
                messages.success(request, 'Notlar başarıyla kaydedildi.')
            except (ValueError, Exception) as e:
                messages.error(request, f'Notları kaydederken bir hata oluştu: {e}')
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

    # Learning outcome skorlarını hesapla (her öğrenci için)
    all_outcome_weights = OutcomeWeight.objects.filter(component__in=components).select_related('component', 'outcome')
    comp_lo_weight_map = {(w.component_id, w.outcome_id): w.weight for w in all_outcome_weights}
    
    student_lo_scores = []
    for student in students:
        student_lo_data = []
        for outcome in outcomes:
            lo_weighted_score = Decimal('0.0')
            lo_total_weight = Decimal('0.0')
            
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
                student_lo_data.append({
                    'outcome': outcome,
                    'score': float(lo_score.quantize(Decimal('0.01')))
                })
            else:
                student_lo_data.append({
                    'outcome': outcome,
                    'score': None
                })
        
        student_lo_scores.append({
            'student': student,
            'lo_scores': student_lo_data
        })

    context = {
        'course': course,
        'components': components,
        'outcomes': outcomes,
        'students': students,
        'student_grade_rows': student_grade_rows,
        'student_lo_scores': student_lo_scores,

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
        outcomes = course.learning_outcomes.all()

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

        # Learning outcome skorlarını hesapla
        all_outcome_weights = OutcomeWeight.objects.filter(component__in=components).select_related('component', 'outcome')
        comp_lo_weight_map = {(w.component_id, w.outcome_id): w.weight for w in all_outcome_weights}
        
        learning_outcome_scores = []
        for outcome in outcomes:
            lo_weighted_score = Decimal('0.0')
            lo_total_weight = Decimal('0.0')
            
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
                learning_outcome_scores.append({
                    'outcome': outcome,
                    'score': float(lo_score.quantize(Decimal('0.01')))
                })
            else:
                learning_outcome_scores.append({
                    'outcome': outcome,
                    'score': None
                })

        course_data.append({
            'course': course,
            'component_grade_list': component_grade_list,
            'final_grade': total_score.quantize(Decimal('0.01')),
            'learning_outcome_scores': learning_outcome_scores,
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
            student = form.cleaned_data['student']
            score = form.cleaned_data['score']
            
            grade, created = Grade.objects.get_or_create(
                student=student,
                component=component,
                defaults={'score': score}
            )
            
            if not created:
                grade.score = score
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
    outcomes = course.learning_outcomes.all()

    grade_map = {g.component_id: g.score for g in grades}

    component_grade_list = []
    for comp in components:
        component_grade_list.append({
            "name": comp.name,
            "percentage": comp.percentage,
            "score": grade_map.get(comp.id)
        })

    # Learning outcome skorlarını hesapla
    all_outcome_weights = OutcomeWeight.objects.filter(component__in=components).select_related('component', 'outcome')
    comp_lo_weight_map = {(w.component_id, w.outcome_id): w.weight for w in all_outcome_weights}
    
    learning_outcome_scores = []
    learning_outcome_score_map = {}
    for outcome in outcomes:
        lo_weighted_score = Decimal('0.0')
        lo_total_weight = Decimal('0.0')
        
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
            lo_score = lo_score.quantize(Decimal('0.01'))
            learning_outcome_score_map[outcome.id] = lo_score
            learning_outcome_scores.append({
                'outcome': outcome,
                'score': float(lo_score)
            })
        else:
            learning_outcome_scores.append({
                'outcome': outcome,
                'score': None
            })

    # Program outcome skorları
    lo_po_weights = LearningOutcomeProgramOutcomeWeight.objects.filter(
        learning_outcome__in=outcomes
    ).select_related('program_outcome')

    po_score_map = {}
    for weight_obj in lo_po_weights:
        lo_score = learning_outcome_score_map.get(weight_obj.learning_outcome_id)
        if lo_score is None:
            continue

        po_entry = po_score_map.setdefault(
            weight_obj.program_outcome_id,
            {
                'program_outcome': weight_obj.program_outcome,
                'weighted_sum': Decimal('0.0'),
                'total_weight': Decimal('0.0')
            }
        )

        weight_decimal = Decimal(weight_obj.weight)
        po_entry['weighted_sum'] += lo_score * weight_decimal
        po_entry['total_weight'] += weight_decimal

    program_outcome_scores = []
    for entry in po_score_map.values():
        if entry['total_weight'] > 0:
            score = (entry['weighted_sum'] / entry['total_weight']).quantize(Decimal('0.01'))
            program_outcome_scores.append({
                'program_outcome': entry['program_outcome'],
                'score': float(score)
            })
        else:
            program_outcome_scores.append({
                'program_outcome': entry['program_outcome'],
                'score': None
            })

    context = {
        "course": course,
        "component_grade_list": component_grade_list,
        "learning_outcome_scores": learning_outcome_scores,
        "program_outcome_scores": program_outcome_scores,
    }

    return render(request, "course_management/student_course_detail.html", context)


@login_required
@user_is_instructor
def instructor_manage_component_outcomes(request, course_id=None):
    if course_id:
        courses = Course.objects.filter(id=course_id, instructors=request.user).prefetch_related('evaluation_components', 'learning_outcomes')
    else:
        courses = Course.objects.filter(instructors=request.user).prefetch_related('evaluation_components', 'learning_outcomes')
    
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
                outcome_rows.append({
                    'outcome': outcome,
                    'weight': weight_map.get(outcome.id)
                })
            
            component_data.append({
                'component': component,
                'outcome_rows': outcome_rows
            })
        
        course_data.append({
            'course': course,
            'component_data': component_data,
            'outcomes': outcomes
        })
    
    if request.method == 'POST':
        component_id = request.POST.get('component_id')
        component = get_object_or_404(
            EvaluationComponent,
            id=component_id,
            course__instructors=request.user
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
                    defaults={'weight': value_int}
                )
            else:
                OutcomeWeight.objects.filter(
                    component=component,
                    outcome=outcome
                ).delete()
        
        messages.success(request, "Ağırlıklar başarıyla güncellendi.")
        if course_id:
            return redirect('instructor_manage_course_component_outcomes', course_id=course_id)
        else:
            return redirect('instructor_manage_component_outcomes')
    
    context = {
        'course_data': course_data,
    }
    return render(request, 'course_management/instructor_manage_component_outcomes.html', context)


@login_required
@user_is_department_head
def department_head_manage_lo_po_weights(request):
    all_courses = Course.objects.all().prefetch_related('learning_outcomes')
    all_program_outcomes = ProgramOutcome.objects.all().order_by('code')
    
    course_data = []
    for course in all_courses:
        outcomes = course.learning_outcomes.all()
        
        outcome_data = []
        for outcome in outcomes:
            existing_weights = LearningOutcomeProgramOutcomeWeight.objects.filter(learning_outcome=outcome)
            weight_map = {w.program_outcome_id: w.weight for w in existing_weights}
            
            po_rows = []
            for po in all_program_outcomes:
                po_rows.append({
                    'program_outcome': po,
                    'weight': weight_map.get(po.id)
                })
            
            outcome_data.append({
                'outcome': outcome,
                'po_rows': po_rows
            })
        
        course_data.append({
            'course': course,
            'outcome_data': outcome_data
        })
    
    if request.method == 'POST':
        outcome_id = request.POST.get('outcome_id')
        outcome = get_object_or_404(LearningOutcome, id=outcome_id)
        
        for po in all_program_outcomes:
            field_name = f"weight_{outcome_id}_{po.id}"
            value = request.POST.get(field_name)
            
            if value:
                value_int = int(value)
                LearningOutcomeProgramOutcomeWeight.objects.update_or_create(
                    learning_outcome=outcome,
                    program_outcome=po,
                    defaults={'weight': value_int}
                )
            else:
                LearningOutcomeProgramOutcomeWeight.objects.filter(
                    learning_outcome=outcome,
                    program_outcome=po
                ).delete()
        
        messages.success(request, "Ağırlıklar başarıyla güncellendi.")
        return redirect('department_head_manage_lo_po_weights')
    
    context = {
        'course_data': course_data,
        'all_program_outcomes': all_program_outcomes,
    }
    return render(request, 'course_management/department_head_manage_lo_po_weights.html', context)


@login_required
@user_is_department_head
def department_head_view_outcomes(request):
    all_courses = Course.objects.all().prefetch_related('learning_outcomes', 'evaluation_components')
    all_program_outcomes = ProgramOutcome.objects.all().order_by('code')
    
    course_data = []
    for course in all_courses:
        components = course.evaluation_components.all()
        outcomes = course.learning_outcomes.all()
        
        component_lo_data = []
        for component in components:
            weights = OutcomeWeight.objects.filter(component=component).select_related('outcome')
            component_lo_data.append({
                'component': component,
                'weights': weights
            })
        
        lo_po_data = []
        for outcome in outcomes:
            weights = LearningOutcomeProgramOutcomeWeight.objects.filter(learning_outcome=outcome).select_related('program_outcome')
            lo_po_data.append({
                'outcome': outcome,
                'weights': weights
            })
        
        course_data.append({
            'course': course,
            'component_lo_data': component_lo_data,
            'lo_po_data': lo_po_data
        })
    
    context = {
        'course_data': course_data,
        'all_program_outcomes': all_program_outcomes,
    }
    return render(request, 'course_management/department_head_view_outcomes.html', context)


@login_required
@user_is_department_head
def department_head_program_outcome_achievement(request):
    all_courses = Course.objects.all().prefetch_related(
        'learning_outcomes',
        'evaluation_components',
        'students'
    )
    all_program_outcomes = ProgramOutcome.objects.all().order_by('code')
    all_students = User.objects.filter(profile__role='student').prefetch_related('enrolled_courses', 'grades')
    
    all_grades = Grade.objects.select_related('student', 'component').filter(
        student__profile__role='student',
        score__isnull=False
    )
    grade_map = {(g.student_id, g.component_id): g.score for g in all_grades}
    
    all_outcome_weights = OutcomeWeight.objects.select_related('component', 'outcome').all()
    comp_lo_weight_map = {(w.component_id, w.outcome_id): w.weight for w in all_outcome_weights}
    
    all_lo_po_weights = LearningOutcomeProgramOutcomeWeight.objects.select_related(
        'learning_outcome', 'program_outcome'
    ).all()
    lo_po_weight_map = {(w.learning_outcome_id, w.program_outcome_id): w.weight for w in all_lo_po_weights}
    
    po_achievement_data = []
    
    for po in all_program_outcomes:
        student_po_scores = []
        
        for student in all_students:
            student_po_score = Decimal('0.0')
            student_po_weight = Decimal('0.0')
            
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
                    
                    lo_weighted_score = Decimal('0.0')
                    lo_total_weight = Decimal('0.0')
                    
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
        
        po_achievement_data.append({
            'program_outcome': po,
            'average_score': average_score,
            'min_score': min_score,
            'max_score': max_score,
            'student_count': student_count,
        })
    
    context = {
        'po_achievement_data': po_achievement_data,
    }
    return render(request, 'course_management/department_head_program_outcome_achievement.html', context)


@login_required
@user_is_department_head
def delete_program_outcome(request, outcome_id):
    program_outcome = get_object_or_404(ProgramOutcome, id=outcome_id)

    if request.method == 'POST':
        program_outcome.delete()
        messages.success(request, f'"{program_outcome.code}" program outcome\'ı başarıyla silindi.')
    else:
        messages.error(request, 'Program outcome silme isteği başarısız oldu.')

    return redirect('department_head_dashboard')


@login_required
@user_is_department_head
def edit_program_outcome(request, outcome_id):
    program_outcome = get_object_or_404(ProgramOutcome, id=outcome_id)

    if request.method == 'POST':
        form = ProgramOutcomeForm(request.POST, instance=program_outcome)
        if form.is_valid():
            form.save()
            messages.success(request, f'"{program_outcome.code}" program outcome\'ı güncellendi.')
            return redirect('department_head_dashboard')
        else:
            messages.error(request, 'Program outcome güncellenirken bir hata oluştu. Lütfen formu kontrol edin.')
    else:
        form = ProgramOutcomeForm(instance=program_outcome)

    context = {
        'form': form,
        'program_outcome': program_outcome,
    }
    return render(request, 'course_management/edit_program_outcome.html', context)
