from django.db import models
from django.contrib.auth.models import User     # <--  size zoomda bahsettiğim djangonun kendi
from django.conf import settings                     # user modeli ama biz bu modeli genişleteceğiz


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

    syllabus = models.FileField(
        upload_to='course_syllabus/',  # dosyalar 'media/course_syllabus/' klasörüne yüklenecek
        blank=True,
        null=True,
        verbose_name="Ders Syllabus Dosyası (.pdf, .docx vb.)"
    )

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
                                                                             # her bileşeni unique yaptım

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


class ProgramOutcome(models.Model):
    """bölüm program çıktısı"""
    code = models.CharField(max_length=10, unique=True, verbose_name="Çıktı Kodu (örn: PO-1)")
    description = models.TextField(verbose_name="Program Çıktısı Açıklaması")

    class Meta:
        verbose_name = "Program Çıktısı"
        verbose_name_plural = "Program Çıktıları"
        ordering = ['code']  # koda göre sırala

    def __str__(self):
        # açıklamanın ilk 50 karakterini göster
        return f"{self.code}: {self.description[:50]}..."

class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    student_number = models.CharField(max_length=20, unique=True)
    department = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.user.username} - {self.student_number}"
   














class OutcomeWeight(models.Model):
    """
    Bir EvaluationComponent'in (Vize, Final vb.)
    hangi LearningOutcome ile ne kadar ilişkili olduğunu tutar (1-5 arası ağırlık).
    """
    component = models.ForeignKey(
        EvaluationComponent,
        on_delete=models.CASCADE,
        related_name="outcome_weights",
        verbose_name="Değerlendirme Bileşeni"
    )
    outcome = models.ForeignKey(
        LearningOutcome,
        on_delete=models.CASCADE,
        related_name="outcome_weights",
        verbose_name="Learning Outcome"
    )

    weight = models.IntegerField(
        default=1,
        choices=[(1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5')],
        verbose_name="Ağırlık (1-5)"
    )

    class Meta:
        unique_together = ('component', 'outcome')
        verbose_name = "Outcome Ağırlığı"
        verbose_name_plural = "Outcome Ağırlıkları"

    def __str__(self):
        return f"{self.component} ⇄ {self.outcome} (Ağırlık: {self.weight})"
