from django import forms
from .models import (
    EvaluationComponent,
    LearningOutcome,
    Course,
    ProgramOutcome,
    # yeni model ve not modeli:
    OutcomeWeight,
    Grade,
)
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
    """Bölüm başkanının ders + hoca + öğrenci ataması birlikte yapılması için birleşik form"""

    instructor = forms.ModelChoiceField(
        queryset=User.objects.filter(profile__role='instructor')
        .order_by('last_name', 'first_name'),
        required=False,
        label="Öğretim Görevlisi",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    students = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(profile__role='student')
        .order_by('last_name', 'first_name'),
        required=False,
        label="Öğrenciler",
        widget=forms.CheckboxSelectMultiple()
    )

    class Meta:
        model = Course
        fields = ['course_code', 'course_name']
        labels = {
            'course_code': 'Ders Kodu (örn: CSE311)',
            'course_name': 'Ders Adı (örn: Yazılım Mühendisliği)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['instructor'].label_from_instance = (
            lambda obj: obj.get_full_name() or obj.username
        )
        self.fields['students'].label_from_instance = (
            lambda obj: obj.get_full_name() or obj.username
        )

    def clean_course_code(self):
        """Aynı ders kodu tekrar eklenmesin"""
        course_code = self.cleaned_data['course_code'].strip().upper()

        if Course.objects.filter(course_code=course_code).exists():
            raise forms.ValidationError(
                "Bu ders kodu ile zaten bir ders mevcut."
            )

        return course_code
    
    def save(self, commit=True):
        course = super().save(commit=False)

        instructor = self.cleaned_data.get('instructor')
        students = self.cleaned_data.get('students')

        if commit:
           course.save()

        if instructor:
            course.instructors.add(instructor)

        if students:
            course.students.set(students)

        return course



class SyllabusForm(forms.ModelForm):
    """hocanın ders syllabus dosyasını yüklemesi için form"""
    class Meta:
        model = Course
        fields = ['syllabus']
        labels = {
            'syllabus': 'Syllabus Dosyası Yükle'
        }
        widgets = {
            # FileInput widgetı kullanıyoruz dosyanın türünü kontrol etmek için, bu da djangonun kendi özelliği
            'syllabus': forms.ClearableFileInput(attrs={'class': 'form-control-file'}),
        }


class ProgramOutcomeForm(forms.ModelForm):
    """bölüm başkanının program çıktısı eklemesi için form"""
    class Meta:
        model = ProgramOutcome
        fields = ['code', 'description']
        labels = {
            'code': 'Çıktı Kodu (örn: PO-1, PO-2)',
            'description': 'Program Çıktısının Açıklaması',
        }
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }


class GradeForm(forms.ModelForm):
    """
    Hocanın bir değerlendirme bileşeni (Vize/Final) için
    bir öğrencinin notunu girmesi için form.
    """
    class Meta:
        model = Grade
        fields = ['student', 'score']
        labels = {
            'student': 'Öğrenci',
            'score': 'Not',
        }
        widgets = {
            'student': forms.Select(attrs={'class': 'form-control'}),
            'score': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100}),
        }

    def __init__(self, *args, **kwargs):
        """
        course parametresi alacağız ve öğrenci listesini
        sadece o derse kayıtlı öğrencilerle sınırlayacağız.
        """
        course = kwargs.pop('course', None)
        super().__init__(*args, **kwargs)

        if course is not None:
            # Sadece o derse kayıtlı öğrenciler görünsün
            self.fields['student'].queryset = course.students.all().order_by('last_name', 'first_name')

class GradeUploadForm(forms.Form):
    file = forms.FileField(label="Excel Dosyası")


class InstructorCourseEditForm(forms.Form):
    """
    Bölüm başkanının, bir hocanın verdiği dersleri
    topluca düzenlemesi için form.
    """
    courses = forms.ModelMultipleChoiceField(
        queryset=Course.objects.all().order_by('course_code'),
        required=False,
        label="Verdiği Dersler",
        widget=forms.CheckboxSelectMultiple
    )

    def __init__(self, *args, **kwargs):
        instructor = kwargs.pop("instructor", None)
        super().__init__(*args, **kwargs)
        # Listeyi daha okunabilir yap
        self.fields["courses"].label_from_instance = (
            lambda obj: f"{obj.course_code} – {obj.course_name}"
        )
        # Eğer instructor verilmişse başlangıçta onun derslerini işaretle
        if instructor is not None:
            self.fields["courses"].initial = instructor.courses_taught.all()
