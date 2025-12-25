from decimal import Decimal, InvalidOperation
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from course_management.decorators import user_is_instructor
from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model
User = get_user_model()
import pandas as pd
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
                return redirect("course_home", course_id=course.id)

        elif "submit_outcome" in request.POST:
            outcome_form = LearningOutcomeForm(request.POST)
            if outcome_form.is_valid():
                outcome = outcome_form.save(commit=False)
                outcome.course = course
                outcome.save()
                messages.success(request, "Öğrenim çıktısı başarıyla eklendi.")
                return redirect("course_home", course_id=course.id)

        elif "submit_syllabus" in request.POST:
            syllabus_form = SyllabusForm(request.POST, request.FILES, instance=course)
            if syllabus_form.is_valid():
                syllabus_form.save()
                messages.success(request, "Syllabus dosyası başarıyla güncellendi.")
                return redirect("course_home", course_id=course.id)
            else:
                messages.error(request, "Dosya yüklenirken bir hata oluştu. Lütfen geçerli bir dosya seçin.")

        elif "submit_grades" in request.POST:
            try:
                for key, value in request.POST.items():
                    if not key.startswith("grade_"):
                        continue

                    parts = key.split("_")
                    if len(parts) != 3:
                        continue

                    _, student_id, component_id = parts
                    score_value = value.strip() if value else ""

                    if score_value:
                        try:
                            score_decimal = Decimal(score_value)
                            if not (Decimal("0") <= score_decimal <= Decimal("100")):
                                continue
                        except (ValueError, InvalidOperation):
                            continue
                    else:
                        score_decimal = None

                    grade, _ = Grade.objects.get_or_create(
                        student_id=student_id,
                        component_id=component_id
                    )
                    grade.score = score_decimal
                    grade.save()

                messages.success(request, "Notlar başarıyla kaydedildi.")
            except Exception as e:
                messages.error(request, f"Notları kaydederken bir hata oluştu: {e}")

            return redirect("course_home", course_id=course.id)

    grade_map = {
        (g.student_id, g.component_id): g.score
        for g in Grade.objects.filter(component__in=components, student__in=students)
    }

    student_grade_rows = [
        {
            "student_object": s,
            "grades_list": [
                {"component_id": c.id, "score": grade_map.get((s.id, c.id))}
                for c in components
            ],
        }
        for s in students
    ]

    comp_lo_weight_map = {
        (w.component_id, w.outcome_id): w.weight
        for w in OutcomeWeight.objects.filter(component__in=components).select_related("component", "outcome")
    }

    student_lo_scores = []
    for student in students:
        student_lo_data = []
        for outcome in outcomes:
            lo_weighted_score = Decimal("0")
            lo_total_weight = Decimal("0")

            for c in components:
                score = grade_map.get((student.id, c.id))
                weight = comp_lo_weight_map.get((c.id, outcome.id))
                if score is None or weight is None:
                    continue
                lo_weighted_score += Decimal(score) * Decimal(weight)
                lo_total_weight += Decimal(weight)

            student_lo_data.append({
                "outcome": outcome,
                "score": float((lo_weighted_score / lo_total_weight).quantize(Decimal("0.01"))) if lo_total_weight > 0 else None
            })

        student_lo_scores.append({"student": student, "lo_scores": student_lo_data})

    return render(
        request,
        "teacher/course_manage_detail.html",
        {
            "course": course,
            "components": components,
            "outcomes": outcomes,
            "students": students,
            "student_grade_rows": student_grade_rows,
            "student_lo_scores": student_lo_scores,
            "eval_form": eval_form,
            "outcome_form": outcome_form,
            "syllabus_form": syllabus_form,
            "active_tab": "manage",
        },
    )


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
            return redirect("course_lo_add", course_id=course.id)

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
            return redirect("course_eval_add", course_id=course.id)

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
    return render(request, "teacher/instructor_manage_outcomes.html", {
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
def manage_component_weights(request, course_id=None):
    if not course_id:
        return redirect("instructor_dashboard")

    course = get_object_or_404(Course, id=course_id, instructors=request.user)
    course = Course.objects.filter(id=course.id).prefetch_related(
        "evaluation_components", "learning_outcomes"
    ).first()

    components = course.evaluation_components.all()
    outcomes = course.learning_outcomes.all()

    component_data = []
    for component in components:
        weight_map = {
            w.outcome_id: w.weight
            for w in OutcomeWeight.objects.filter(component=component)
        }
        component_data.append({
            "component": component,
            "outcome_rows": [{"outcome": o, "weight": weight_map.get(o.id)} for o in outcomes],
        })

    course_data = [{
        "course": course,
        "component_data": component_data,
        "outcomes": outcomes,
    }]

    if request.method == "POST":
        component = get_object_or_404(
            EvaluationComponent,
            id=request.POST.get("component_id"),
            course=course
        )

        for outcome in outcomes:
            key = f"weight_{component.id}_{outcome.id}"
            value = request.POST.get(key)

            if value is not None and str(value).strip() != "":
                OutcomeWeight.objects.update_or_create(
                    component=component,
                    outcome=outcome,
                    defaults={"weight": int(value)}
                )
            else:
                OutcomeWeight.objects.filter(component=component, outcome=outcome).delete()

        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"success": True, "message": "Ağırlıklar başarıyla güncellendi."})

        messages.success(request, "Ağırlıklar başarıyla güncellendi.")
        return redirect("course_weights", course_id=course.id)

    return render(
        request,
        "teacher/instructor_manage_outcomes.html",
        {
            "course": course,
            "course_data": course_data,
            "active_tab": "weights",
        },
    )


@login_required
@user_is_instructor # Bölüm başkanının yapacağı bir işlem varsayıyorum, gerekiyorsa yetkiyi kontrol edin
def upload_grades(request, course_id):
    """Excel dosyası yükleyerek notları sisteme toplu kaydetme/güncelleme."""
    # Sizin form tanımınız GradeUploadForm() olduğu varsayılmıştır.
    # Bu formun sadece bir FileField içerdiği varsayılmıştır.
    from course_management.forms import GradeUploadForm

    course = get_object_or_404(Course, id=course_id, instructors=request.user)

    if request.method == "POST":
        form = GradeUploadForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES["file"]

            # Not: Excel dosyasını okumak için pd.read_excel kullanıyoruz.
            # Yüklediğiniz örnek dosya CSV idi, eğer CSV yüklüyorsanız burayı pd.read_csv olarak değiştirin.
            try:
                df = pd.read_excel(file)
            except Exception as e:
                messages.error(request, f"Dosya okunamadı veya formatı hatalı: {e}")
                return redirect("upload_grades", course_id=course.id)

            kayit_sayisi = 0
            eslesmeyen_ogrenciler = []

            # DataFrame içindeki her satırı (öğrenci/not kaydı) döngüye alıyoruz
            for index, row in df.iterrows():
                # Alanların boş olup olmadığını kontrol ediyoruz
                if not row.get('username') or not row.get('component_name') or row.get('score') is None:
                    messages.warning(request, f"{index + 2}. satırda eksik veri var ve atlandı.")
                    continue

                try:
                    # Eşleştirme anahtarı olarak username'i kullanıyoruz (Tavsiye edilen yol)
                    student_username = str(row['username']).strip()
                    component_name = str(row['component_name']).strip()
                    score = float(row['score'])

                    # 1. Kullanıcı Adı ile öğrenciyi bul (User Modelini Kullanarak)
                    # Not: User modelinin username alanı benzersizdir ve güvenilir bir eşleştirme sağlar.
                    student_user = User.objects.get(username=student_username)

                    # 2. Not bileşenini bul (Vize, Final, Ödev vb.)
                    component = EvaluationComponent.objects.get(name=component_name)

                    # 3. Notu kaydet veya güncelle (Zaten varsa üzerine yazar)
                    Grade.objects.update_or_create(
                        student=student_user,
                        component=component,
                        defaults={'score': score}
                    )

                    kayit_sayisi += 1

                except User.DoesNotExist:
                    # Kullanıcı adı veritabanında bulunamazsa
                    eslesmeyen_ogrenciler.append(student_username)
                except EvaluationComponent.DoesNotExist:
                    # Excel'deki not bileşeni adı (vize1, final vb.) sistemde tanımlı değilse
                    messages.warning(request, f"'{component_name}' adında Not Bileşeni bulunamadı ve not işlenemedi.")
                except ValueError:
                    # Not (score) alanı sayıya çevrilemezse
                    messages.error(request, f"Hata: {student_username} kullanıcısının notu sayısal değil.")
                except Exception as e:
                    # Diğer tüm hatalar
                    messages.error(request, f"Beklenmedik bir hata oluştu: {e}")

            # Eşleşmeyen öğrencileri toplu halde raporla
            if eslesmeyen_ogrenciler:
                messages.warning(request,
                                 f"Aşağıdaki {len(eslesmeyen_ogrenciler)} kullanıcı adına ait öğrenci sistemde bulunamadı ve notları işlenmedi: "
                                 f"{', '.join(eslesmeyen_ogrenciler[:10])}{' ve daha fazlası...' if len(eslesmeyen_ogrenciler) > 10 else ''}"
                                 )

            messages.success(request, f"Başarıyla {kayit_sayisi} not sisteme işlendi.")
            return redirect("upload_grades", course_id=course.id)
    else:
        # Formun yüklenmesi
        form = GradeUploadForm()

    return render(request, "teacher/upload_grades.html", {"form": form, "course": course})


def instructor_csv_upload_placeholder(request, course_id):
    return render(request, "teacher/csv_upload_placeholder.html", {"course_id": course_id})

@login_required
@user_is_instructor
def course_home(request, course_id):
    return manage_course(request, course_id)

@login_required
@user_is_instructor
def course_outcomes(request, course_id):
    course = get_object_or_404(Course, id=course_id, instructors=request.user)

    if request.method == "POST":
        form = LearningOutcomeForm(request.POST)
        if form.is_valid():
            lo = form.save(commit=False)
            lo.course = course
            lo.save()
            messages.success(request, "Öğrenim çıktısı başarıyla eklendi.")
            return redirect("course_lo_add", course_id=course.id)
    else:
        form = LearningOutcomeForm()

    return render(request, "teacher/add_learning_outcome.html", {
        "course": course,
        "form": form,
        "active_tab": "lo",
    })


@login_required
@user_is_instructor
def course_components(request, course_id):
    course = get_object_or_404(Course, id=course_id, instructors=request.user)

    if request.method == "POST":
        form = EvaluationComponentForm(request.POST)
        if form.is_valid():
            comp = form.save(commit=False)
            comp.course = course
            comp.save()
            messages.success(request, "Değerlendirme bileşeni başarıyla eklendi.")
            return redirect("course_eval_add", course_id=course.id)
    else:
        form = EvaluationComponentForm()

    return render(request, "teacher/add_evaluation_component.html", {
        "course": course,
        "form": form,
        "active_tab": "eval",
    })

@login_required
@user_is_instructor
def course_weights(request, course_id):
    return manage_component_weights(request, course_id=course_id)

@login_required
@user_is_instructor
def edit_component(request, course_id, component_id):
    """Mevcut değerlendirme bileşenini (vize/final vs.) düzenleme."""
    course = get_object_or_404(Course, id=course_id, instructors=request.user)
    component = get_object_or_404(EvaluationComponent, id=component_id, course=course)

    if request.method == "POST":
        form = EvaluationComponentForm(request.POST, instance=component)
        if form.is_valid():
            form.save()
            messages.success(request, "Değerlendirme bileşeni güncellendi.")
            return redirect("course_home", course_id=course.id)
    else:
        form = EvaluationComponentForm(instance=component)

    return render(
        request,
        "teacher/add_evaluation_component.html",  # yeni template açmak istemezsen mevcut form sayfasını kullanıyoruz
        {
            "course": course,
            "form": form,
            "component": component,
            "active_tab": "eval",
        },
    )


@login_required
@user_is_instructor
def delete_component(request, course_id, component_id):
    """Değerlendirme bileşenini siler."""
    course = get_object_or_404(Course, id=course_id, instructors=request.user)
    component = get_object_or_404(EvaluationComponent, id=component_id, course=course)

    if request.method == "POST":
        name = component.name
        component.delete()
        messages.success(request, f"'{name}' bileşeni silindi.")
        return redirect("course_home", course_id=course.id)

    # GET ile gelinirse direkt derse geri gönder (ayrı confirm sayfası istemiyorsan)
    return redirect("course_home", course_id=course.id)

@login_required
@user_is_instructor
def edit_outcome(request, course_id, outcome_id):
    course = get_object_or_404(Course, id=course_id, instructors=request.user)
    outcome = get_object_or_404(LearningOutcome, id=outcome_id, course=course)

    if request.method == "POST":
        form = LearningOutcomeForm(request.POST, instance=outcome)
        if form.is_valid():
            form.save()
            messages.success(request, "Learning outcome güncellendi.")
            return redirect("course_home", course_id=course.id)
    else:
        form = LearningOutcomeForm(instance=outcome)

    return render(
        request,
        "teacher/add_learning_outcome.html",
        {"course": course, "form": form, "outcome": outcome},
    )


@login_required
@user_is_instructor
def delete_outcome(request, course_id, outcome_id):
    course = get_object_or_404(Course, id=course_id, instructors=request.user)
    outcome = get_object_or_404(LearningOutcome, id=outcome_id, course=course)

    if request.method == "POST":
        name = outcome.description[:40]
        outcome.delete()
        messages.success(request, f"Outcome silindi: {name}")
        return redirect("course_home", course_id=course.id)

    return redirect("course_home", course_id=course.id)
