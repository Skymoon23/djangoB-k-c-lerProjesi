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