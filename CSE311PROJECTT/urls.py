from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from course_management.views import RoleBasedLoginView

urlpatterns = [
    path('admin/', admin.site.urls),

    # custom role-based login (Django'nun built-in login'inden önce gelmeli)
    path('accounts/login/', RoleBasedLoginView.as_view(), name='login'),
    
    # hazır auth (login/logout) URL'leri (login hariç, çünkü yukarıda override ettik)
    path('accounts/', include('django.contrib.auth.urls')),

    # ortak home + dashboard yönlendirme
    path('', include('course_management.urls')),

    # rol bazlı app'ler
    path('student/', include('student.urls')),
    path('instructor/', include('teacher.urls')),
    path('department/', include('headteacher.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
