from decimal import Decimal
from django.contrib.auth.models import User
from django.test import TestCase
from course_management.forms import (
    CourseCreateForm, InstructorAssignForm, StudentAssignForm,
    ProgramOutcomeForm, EvaluationComponentForm, LearningOutcomeForm,
    GradeForm
)
from course_management.models import (
    Profile, Course, EvaluationComponent, LearningOutcome
)


class CourseCreateFormTest(TestCase):
    """CourseCreateForm testleri"""
    
    def test_course_create_form_valid(self):
        """Geçerli course oluşturma formu"""
        form_data = {
            'course_code': 'CSE311',
            'course_name': 'Software Engineering'
        }
        form = CourseCreateForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_course_create_form_save(self):
        """Form kaydetme testi"""
        form_data = {
            'course_code': 'CSE311',
            'course_name': 'Software Engineering'
        }
        form = CourseCreateForm(data=form_data)
        self.assertTrue(form.is_valid())
        course = form.save()
        self.assertEqual(course.course_code, 'CSE311')
        self.assertEqual(course.course_name, 'Software Engineering')


class InstructorAssignFormTest(TestCase):
    """InstructorAssignForm testleri"""
    
    def setUp(self):
        self.course = Course.objects.create(
            course_code='CSE311',
            course_name='Software Engineering'
        )
        self.instructor = User.objects.create_user(
            username='instructor',
            password='testpass123',
            first_name='Instructor',
            last_name='User'
        )
        profile, _ = Profile.objects.get_or_create(user=self.instructor)
        profile.role = 'instructor'
        profile.save()
    
    def test_instructor_assign_form_valid(self):
        """Geçerli instructor atama formu"""
        form_data = {
            'course': self.course.id,
            'instructor': self.instructor.id
        }
        form = InstructorAssignForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_instructor_assign_form_only_instructors(self):
        """Form sadece instructor rolündeki kullanıcıları gösterir"""
        student = User.objects.create_user(
            username='student',
            password='testpass123'
        )
        profile, _ = Profile.objects.get_or_create(user=student)
        profile.role = 'student'
        profile.save()
        
        form = InstructorAssignForm()
        instructor_ids = [instructor.id for instructor in form.fields['instructor'].queryset]
        self.assertIn(self.instructor.id, instructor_ids)
        self.assertNotIn(student.id, instructor_ids)


class StudentAssignFormTest(TestCase):
    """StudentAssignForm testleri"""
    
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
    
    def test_student_assign_form_valid(self):
        """Geçerli student atama formu"""
        form_data = {
            'course': self.course.id,
            'student': self.student.id
        }
        form = StudentAssignForm(data=form_data)
        self.assertTrue(form.is_valid())


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

