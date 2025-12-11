from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.shortcuts import redirect, render

from .models import Profile


def home(request):
    return render(request, "registration/home.html")


class RoleBasedLoginView(LoginView):
    """
    Role-based login view. Kullanıcının seçtiği role ile
    gerçek rolünü karşılaştırır.
    """
    template_name = 'registration/login.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        selected_role = self.request.GET.get('role', '')
        
        # Role display mapping
        role_display_map = {
            'department_head': 'Bölüm Başkanı',
            'instructor': 'Öğretim Görevlisi',
            'student': 'Öğrenci',
        }
        
        context['selected_role_display'] = role_display_map.get(selected_role, '')
        context['selected_role'] = selected_role
        return context
    
    def get(self, request, *args, **kwargs):
        # Eğer role parametresi yoksa, kullanıcıyı home sayfasına yönlendir
        selected_role = request.GET.get('role', '')
        role_mapping = {
            'department_head': 'department_head',
            'instructor': 'instructor',
            'student': 'student',
        }
        
        if not selected_role or selected_role not in role_mapping:
            # Mesaj göstermeden direkt home'a yönlendir
            return redirect('home')
        
        return super().get(request, *args, **kwargs)
    
    def form_valid(self, form):
        # Kullanıcıyı giriş yaptırır
        user = form.get_user()
        
        # URL'den seçilen role'ü alır
        selected_role = self.request.GET.get('role', '')
        
        # Kullanıcının gerçek rolünü kontrol eder
        try:
            user_role = user.profile.role
        except Profile.DoesNotExist:
            messages.error(
                self.request,
                "Kullanıcı profili bulunamadı. Lütfen yönetici ile iletişime geçin."
            )
            # POST-redirect-GET pattern: role parametresini koruyarak redirect yap
            return redirect(f"{self.request.path}?role={selected_role}")
        
        # Role mapping: URL'deki role ile model'deki role'ü eşleştirir
        role_mapping = {
            'department_head': 'department_head',
            'instructor': 'instructor',
            'student': 'student',
        }
        
        # Seçilen role geçerli mi kontrol eder
        if selected_role not in role_mapping:
            messages.error(
                self.request,
                "Geçersiz role seçimi. Lütfen ana sayfadan tekrar deneyin."
            )
            return redirect('home')
        
        # Kullanıcının gerçek rolü ile seçilen role'ü karşılaştır
        if user_role != role_mapping[selected_role]:
            role_display = user.profile.get_role_display()
            messages.error(
                self.request,
                f"Bu hesap {role_display} rolüne sahip. "
                f"Lütfen doğru role butonunu seçerek tekrar deneyin."
            )
            # POST-redirect-GET pattern: role parametresini koruyarak redirect yap
            return redirect(f"{self.request.path}?role={selected_role}")
        
        # Role eşleşiyorsa normal login işlemini yapar
        login(self.request, user)
        return redirect('dashboard_redirect')


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
            return redirect("admin:index")
        return redirect("login")

    if role == "instructor":
        return redirect("instructor_dashboard")
    elif role == "student":
        return redirect("student_dashboard")
    elif role == "department_head":
        return redirect("department_head_dashboard")
    else:
        return redirect("login")


import pandas as pd
from django.contrib.auth.models import User
from django.shortcuts import HttpResponse

def import_students(request):
    # Excel dosyasının yolu
    file_path = 'students.xlsx'  # projenizin root klasöründe olduğunu varsayıyoruz

    # Excel dosyasını oku
    df = pd.read_excel(file_path)

    # Her satır için kullanıcı oluştur
    for index, row in df.iterrows():
        username = row['username']
        password = row['password']
        first_name = row['first_name']
        last_name = row['last_name']
        student_number = row['student_number']

        # Eğer kullanıcı zaten yoksa
        if not User.objects.filter(username=username).exists():
            user = User.objects.create_user(
                username=username,
                password=password,
                first_name=first_name,
                last_name=last_name,
            )
            # student_number gibi extra alanlarınız varsa
            # user.profile.student_number = student_number
            # user.profile.save()

    return HttpResponse("Öğrenciler başarıyla yüklendi!")


import pandas as pd
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Student, Course, Grade   # modeller seninkiyse
                                             # isimler farklıysa söyle düzenleyeyim

@login_required
def import_grades_from_excel(request):
    if request.method == "POST" and request.FILES.get("excel_file"):

        excel_file = request.FILES["excel_file"]

        try:
            df = pd.read_excel(excel_file)

            required_columns = {"student_number", "course_code", "grade"}
            if not required_columns.issubset(df.columns):
                messages.error(request, "Excel dosyası yanlış formatta!")
                return redirect("import_grades")

            created_count = 0
            updated_count = 0
            errors = []

            for _, row in df.iterrows():
                student_no = str(row["student_number"]).strip()
                course_code = str(row["course_code"]).strip()
                grade_value = row["grade"]

                # ---- Student kontrolü ----
                try:
                    student = Student.objects.get(student_number=student_no)
                except Student.DoesNotExist:
                    errors.append(f"Öğrenci bulunamadı: {student_no}")
                    continue

                # ---- Course kontrolü ----
                try:
                    course = Course.objects.get(course_code=course_code)
                except Course.DoesNotExist:
                    errors.append(f"Ders bulunamadı: {course_code}")
                    continue

                # ---- Not ekleme veya güncelleme ----
                grade_obj, created = Grade.objects.update_or_create(
                    student=student,
                    course=course,
                    defaults={"grade": grade_value}
                )

                if created:
                    created_count += 1
                else:
                    updated_count += 1

            messages.success(
                request,
                f"{created_count} yeni not eklendi, {updated_count} not güncellendi."
            )

            if errors:
                messages.warning(request, f"Hatalı satırlar: {len(errors)}")
                for e in errors:
                    print("Hata:", e)

            return redirect("import_grades")

        except Exception as e:
            messages.error(request, f"Hata oluştu: {str(e)}")
            return redirect("import_grades")

    return render(request, "import_grades.html")
