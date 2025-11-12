from django import forms
from .models import EvaluationComponent, LearningOutcome, Course
from django.contrib.auth import get_user_model

# user modelini al
User = get_user_model()


class EvaluationComponentForm(forms.ModelForm):
    class Meta:
        model = EvaluationComponent
        fields = ['name', 'percentage']
        labels = {
            'name': 'Bileşen Adı (Vize, Final, Proje vb.)',
            'percentage': 'Yüzdelik Ağırlığı',
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'percentage': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100}),
        }


class LearningOutcomeForm(forms.ModelForm):
    class Meta:
        model = LearningOutcome
        fields = ['description']
        labels = {
            'description': 'Öğrenim Çıktısı Açıklaması',
        }
        widgets = {
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class CourseCreateForm(forms.ModelForm):
    """bölüm başkanının yeni ders oluşturması için form"""

    class Meta:
        model = Course
        # sadece bu iki alanla ders oluşturulsun
        fields = ['course_code', 'course_name']
        labels = {
            'course_code': 'Ders Kodu (örn: CSE311)',
            'course_name': 'Ders Adı (örn: Yazılım Mühendisliği)',
        }


class InstructorAssignForm(forms.Form):
    """bölüm başkanının bir derse hoca ataması için form"""

    # tüm dersleri listeleyen bir dropdown
    course = forms.ModelChoiceField(
        queryset=Course.objects.all().order_by('course_code'),
        label="Ders Seçin",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    # sadece instructor rolündeki kullanıcıları listeleyen bir dropdown
    instructor = forms.ModelChoiceField(
        queryset=User.objects.filter(profile__role='instructor').order_by('last_name', 'first_name'),
        label="Öğretim Görevlisi Seçin",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    def __init__(self, *args, **kwargs):
        """Dropdown'larda daha okunaklı isimler göster"""
        super().__init__(*args, **kwargs)
        self.fields['course'].label_from_instance = lambda obj: f"{obj.course_code} - {obj.course_name}"
        self.fields['instructor'].label_from_instance = lambda obj: obj.get_full_name() or obj.username


class StudentAssignForm(forms.Form):
    """bölüm başkanının bir derse öğrenci ataması için form"""

    # tüm dersleri listeleyen bir dropdown
    course = forms.ModelChoiceField(
        queryset=Course.objects.all().order_by('course_code'),
        label="Ders Seçin",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    # sadece student rolündeki kullanıcıları listeleyen bir dropdown
    student = forms.ModelChoiceField(
        queryset=User.objects.filter(profile__role='student').order_by('last_name', 'first_name'),
        label="Öğrenci Seçin",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    def __init__(self, *args, **kwargs):
        """dropdown'larda daha okunaklı isimler göster"""
        super().__init__(*args, **kwargs)
        self.fields['course'].label_from_instance = lambda obj: f"{obj.course_code} - {obj.course_name}"
        self.fields['student'].label_from_instance = lambda obj: obj.get_full_name() or obj.username
