from django.contrib.auth.models import User
from django.test import TestCase
from course_management.forms import (
    CourseCreateForm, ProgramOutcomeForm, EvaluationComponentForm, LearningOutcomeForm,
    GradeForm
)
from course_management.models import EvaluationComponent
from course_management.models import Profile, Course

class CourseCreateFormTest(TestCase):
    def setUp(self):
        # instructor ve öğrenciler oluşturalım (profil rolleri ile)
        self.instructor = User.objects.create_user(username='ins', password='pw')
        profile, _ = Profile.objects.get_or_create(user=self.instructor)
        profile.role = 'instructor'; profile.save()

        self.s1 = User.objects.create_user(username='s1', password='pw')
        profile, _ = Profile.objects.get_or_create(user=self.s1)
        profile.role = 'student'; profile.save()

        self.s2 = User.objects.create_user(username='s2', password='pw')
        profile, _ = Profile.objects.get_or_create(user=self.s2)
        profile.role = 'student'; profile.save()

    def test_save_assign_instructor_and_students(self):
        data = {
            'course_code': 'CSE999',
            'course_name': 'Test Ders',
            'instructor': self.instructor.id,
            'students': [self.s1.id, self.s2.id],
        }
        form = CourseCreateForm(data)
        self.assertTrue(form.is_valid())
        course = form.save()
        self.assertIsNotNone(course.pk)
        self.assertIn(self.instructor, course.instructors.all())
        self.assertSetEqual(set(course.students.values_list('id', flat=True)), {self.s1.id, self.s2.id})

    def test_duplicate_course_code_validation(self):
        Course.objects.create(course_code='CSE100', course_name='Mevcut')
        form = CourseCreateForm({'course_code': 'CSE100', 'course_name': 'Yeni'})
        self.assertFalse(form.is_valid())
        self.assertIn('course_code', form.errors)
        self.assertIn('Bu ders kodu ile zaten bir ders mevcut.', form.errors['course_code'])



class ProgramOutcomeFormTest(TestCase):
    """ProgramOutcomeForm testleri"""
    
    def test_program_outcome_form_valid(self):
        """Geçerli program outcome formu"""
        form_data = {
            'code': 'PO-1',
            'description': 'Test program outcome description'
        }
        form = ProgramOutcomeForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_program_outcome_form_save(self):
        """Form kaydetme testi"""
        form_data = {
            'code': 'PO-1',
            'description': 'Test program outcome description'
        }
        form = ProgramOutcomeForm(data=form_data)
        self.assertTrue(form.is_valid())
        po = form.save()
        self.assertEqual(po.code, 'PO-1')
        self.assertEqual(po.description, 'Test program outcome description')


class EvaluationComponentFormTest(TestCase):
    """EvaluationComponentForm testleri"""
    
    def setUp(self):
        self.course = Course.objects.create(
            course_code='CSE311',
            course_name='Software Engineering'
        )
    
    def test_evaluation_component_form_valid(self):
        """Geçerli evaluation component formu"""
        form_data = {
            'name': 'Midterm',
            'percentage': 40
        }
        form = EvaluationComponentForm(data=form_data)
        self.assertIn('name', form.fields)
        self.assertIn('percentage', form.fields)


class LearningOutcomeFormTest(TestCase):
    """LearningOutcomeForm testleri"""
    def setUp(self):
        self.course = Course.objects.create(
            course_code='CSE311',
            course_name='Software Engineering'
        )
    
    def test_learning_outcome_form_valid(self):
        """Geçerli learning outcome formu"""
        form_data = {
            'description': 'Test learning outcome description'
        }
        form = LearningOutcomeForm(data=form_data)
        self.assertIn('description', form.fields)


class GradeFormTest(TestCase):
    """GradeForm testleri"""
    def setUp(self):
        self.course = Course.objects.create(
            course_code='CSE311',
            course_name='Software Engineering'
        )
        self.student = User.objects.create_user(
            username='student',
            password='testpass123',
            first_name='Student',
            last_name='User'
        )
        profile, _ = Profile.objects.get_or_create(user=self.student)
        profile.role = 'student'
        profile.save()
        self.course.students.add(self.student)
        
        self.component = EvaluationComponent.objects.create(
            course=self.course,
            name='Midterm',
            percentage=40
        )
    
    def test_grade_form_valid(self):
        """Geçerli grade formu"""
        form_data = {
            'student': self.student.id,
            'score': 85.50
        }
        form = GradeForm(data=form_data, course=self.course)
        self.assertTrue(form.is_valid())
    
    def test_grade_form_only_course_students(self):
        """Form sadece derse kayıtlı öğrencileri gösterir"""
        other_student = User.objects.create_user(
            username='otherstudent',
            password='testpass123'
        )
        profile, _ = Profile.objects.get_or_create(user=other_student)
        profile.role = 'student'
        profile.save()
        
        form = GradeForm(course=self.course)
        student_ids = [student.id for student in form.fields['student'].queryset]
        self.assertIn(self.student.id, student_ids)
        self.assertNotIn(other_student.id, student_ids)

