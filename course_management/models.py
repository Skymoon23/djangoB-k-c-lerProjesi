from django.db import models
from django.contrib.auth.models import User  # <--  size zoomda bahsettiğim djangonun kendi user modeli ama
from django.conf import settings             #      biz bu modeli genişleteceğiz


class Profile(models.Model):
    # her kullanıcıya bağlı bir profil oluştur
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    # roller
    ROLE_CHOICES = (
        ('student', 'Öğrenci'),
        ('instructor', 'Öğretim Görevlisi'),
        ('department_head', 'Bölüm Başkanı'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, verbose_name="Kullanıcı Rolü")

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.get_role_display()})"


class Course(models.Model):
    """sistemdeki derslerin ana modeli"""
    course_code = models.CharField(max_length=10, unique=True, verbose_name="Ders Kodu")
    course_name = models.CharField(max_length=255, verbose_name="Ders Adı")

    # derse atanan hocalar
    instructors = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        verbose_name="Derse Atanan Hocalar",
        related_name="courses_taught",
        limit_choices_to={'profile__role': 'instructor'}
    )

    # derse kayıtlı öğrenciler
    students = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        verbose_name="Derse Kayıtlı Öğrenciler",
        related_name="enrolled_courses",
        limit_choices_to={'profile__role': 'student'},
        blank=True  # bir derste hiç öğrenci olmayabilir
    )

    syllabus = models.TextField(blank=True, null=True, verbose_name="Ders Syllabus")

    def __str__(self):
        return f"{self.course_code} - {self.course_name}"


class EvaluationComponent(models.Model):
    """sınav belirleme ve yüzdesini belirleme"""
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="evaluation_components",
                               verbose_name="Ders")
    name = models.CharField(max_length=100, verbose_name="Değerlendirme Adı (örn: Vize, Final, Proje)")
    percentage = models.PositiveSmallIntegerField(verbose_name="Ağırlık Yüzdesi (%)")

    class Meta:
        verbose_name = "Değerlendirme Bileşeni"
        verbose_name_plural = "Değerlendirme Bileşenleri"
        # bir ders için aynı isimde iki bileşen olmasın (örn: 2 tane Vize) --> bu aslında sonradan değişecek fakat
        unique_together = ('course', 'name')                                 # şu an sistem hata vermesin diye
                                                                             # her bileşen unique yaptım

    def __str__(self):
        return f"{self.course.course_code} - {self.name} (%{self.percentage})"


class LearningOutcome(models.Model):
    """dersin learning outcomeını belirleme"""
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="learning_outcomes", verbose_name="Ders")
    description = models.TextField(verbose_name="Öğrenim Çıktısı Açıklaması")

    class Meta:
        verbose_name = "Öğrenim Çıktısı"
        verbose_name_plural = "Öğrenim Çıktıları"

    def __str__(self):
        return f"{self.course.course_code} - Çıktı #{self.id}"


class Grade(models.Model):
    """öğrencinin bir sınav bileşeninden aldığı notu tut"""
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="grades",
        verbose_name="Öğrenci",
        limit_choices_to={'profile__role': 'student'}
    )
    component = models.ForeignKey(
        EvaluationComponent,
        on_delete=models.CASCADE,
        related_name="grades",
        verbose_name="Değerlendirme Bileşeni"
    )
    score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name="Alınan Not",
        # not girilmemiş olma ihtimali --> barış hoca sınavları açıkla artık :))))
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = "Not"
        verbose_name_plural = "Notlar"
        # bir öğrencinin bir sınav bileşeninden sadece bir notu olabilir --> yukarıda belirttiğim sebepten kaynaklı
        unique_together = ('student', 'component')

    def __str__(self):
        return f"{self.student.username} - {self.component.name}: {self.score}"
