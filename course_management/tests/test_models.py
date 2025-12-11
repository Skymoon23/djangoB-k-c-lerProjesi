from decimal import Decimal
from django.contrib.auth.models import User
from django.test import TestCase
from course_management.models import (
    Profile, Course, LearningOutcome, EvaluationComponent,
    Grade, ProgramOutcome, OutcomeWeight, LearningOutcomeProgramOutcomeWeight
)


class ProfileModelTest(TestCase):
    """Profile model testleri"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com',
            first_name='Test',
            last_name='User'
        )
    
    def test_profile_creation(self):
        """Profile oluşturma testi"""
        profile, _ = Profile.objects.get_or_create(user=self.user)
        profile.role = 'student'
        profile.save()
        self.assertEqual(profile.user, self.user)
        self.assertEqual(profile.role, 'student')
        self.assertIn('Öğrenci', str(profile))
    
    def test_profile_role_display(self):
        """Role display testi"""
        profile, _ = Profile.objects.get_or_create(user=self.user)
        profile.role = 'instructor'
        profile.save()
        self.assertEqual(profile.get_role_display(), 'Öğretim Görevlisi')
        
        profile.role = 'department_head'
        profile.save()
        self.assertEqual(profile.get_role_display(), 'Bölüm Başkanı')
    
    def test_profile_str_method(self):
        """Profile __str__ metodu testi"""
        profile, _ = Profile.objects.get_or_create(user=self.user)
        profile.role = 'student'
        profile.save()
        self.assertIn('Test User', str(profile))
        self.assertIn('Öğrenci', str(profile))


class CourseModelTest(TestCase):
    """Course model testleri"""
    
    def setUp(self):
        self.instructor = User.objects.create_user(
            username='instructor',
            password='testpass123',
            first_name='Instructor',
            last_name='User'
        )
        profile, _ = Profile.objects.get_or_create(user=self.instructor)
        profile.role = 'instructor'
        profile.save()
        
        self.student = User.objects.create_user(
            username='student',
            password='testpass123',
            first_name='Student',
            last_name='User'
        )
        profile, _ = Profile.objects.get_or_create(user=self.student)
        profile.role = 'student'
        profile.save()
    
    def test_course_creation(self):
        """Course oluşturma testi"""
        course = Course.objects.create(
            course_code='CSE311',
            course_name='Software Engineering'
        )
        self.assertEqual(course.course_code, 'CSE311')
        self.assertEqual(course.course_name, 'Software Engineering')
        self.assertIn('CSE311', str(course))
    
    def test_course_unique_code(self):
        """Course code unique olmalı"""
        Course.objects.create(course_code='CSE311', course_name='Test Course')
        with self.assertRaises(Exception):
            Course.objects.create(course_code='CSE311', course_name='Another Course')
    
    def test_course_instructor_assignment(self):
        """Course'a instructor atama testi"""
        course = Course.objects.create(
            course_code='CSE311',
            course_name='Software Engineering'
        )
        course.instructors.add(self.instructor)
        self.assertIn(self.instructor, course.instructors.all())
        self.assertEqual(course.instructors.count(), 1)
    
    def test_course_student_enrollment(self):
        """Course'a öğrenci kayıt testi"""
        course = Course.objects.create(
            course_code='CSE311',
            course_name='Software Engineering'
        )
        course.students.add(self.student)
        self.assertIn(self.student, course.students.all())
        self.assertEqual(course.students.count(), 1)


class EvaluationComponentModelTest(TestCase):
    """EvaluationComponent model testleri"""
    
    def setUp(self):
        self.course = Course.objects.create(
            course_code='CSE311',
            course_name='Software Engineering'
        )
    
    def test_evaluation_component_creation(self):
        """EvaluationComponent oluşturma testi"""
        component = EvaluationComponent.objects.create(
            course=self.course,
            name='Midterm',
            percentage=40
        )
        self.assertEqual(component.course, self.course)
        self.assertEqual(component.name, 'Midterm')
        self.assertEqual(component.percentage, 40)
        self.assertIn('Midterm', str(component))
    
    def test_evaluation_component_unique_together(self):
        """Aynı ders için aynı isimde iki component olamaz"""
        EvaluationComponent.objects.create(
            course=self.course,
            name='Midterm',
            percentage=40
        )
        with self.assertRaises(Exception):
            EvaluationComponent.objects.create(
                course=self.course,
                name='Midterm',
                percentage=60
            )


class LearningOutcomeModelTest(TestCase):
    """LearningOutcome model testleri"""
    
    def setUp(self):
        self.course = Course.objects.create(
            course_code='CSE311',
            course_name='Software Engineering'
        )
    
    def test_learning_outcome_creation(self):
        """LearningOutcome oluşturma testi"""
        outcome = LearningOutcome.objects.create(
            course=self.course,
            description='Test learning outcome description'
        )
        self.assertEqual(outcome.course, self.course)
        self.assertEqual(outcome.description, 'Test learning outcome description')
        self.assertIn('CSE311', str(outcome))


class GradeModelTest(TestCase):
    """Grade model testleri"""
    
    def setUp(self):
        self.student = User.objects.create_user(
            username='student',
            password='testpass123'
        )
        profile, _ = Profile.objects.get_or_create(user=self.student)
        profile.role = 'student'
        profile.save()
        
        self.course = Course.objects.create(
            course_code='CSE311',
            course_name='Software Engineering'
        )
        self.component = EvaluationComponent.objects.create(
            course=self.course,
            name='Midterm',
            percentage=40
        )
    
    def test_grade_creation(self):
        """Grade oluşturma testi"""
        grade = Grade.objects.create(
            student=self.student,
            component=self.component,
            score=Decimal('85.50')
        )
        self.assertEqual(grade.student, self.student)
        self.assertEqual(grade.component, self.component)
        self.assertEqual(grade.score, Decimal('85.50'))
    
    def test_grade_unique_together(self):
        """Bir öğrencinin bir component için sadece bir notu olabilir"""
        Grade.objects.create(
            student=self.student,
            component=self.component,
            score=Decimal('85.50')
        )
        with self.assertRaises(Exception):
            Grade.objects.create(
                student=self.student,
                component=self.component,
                score=Decimal('90.00')
            )


class ProgramOutcomeModelTest(TestCase):
    """ProgramOutcome model testleri"""
    
    def test_program_outcome_creation(self):
        """ProgramOutcome oluşturma testi"""
        po = ProgramOutcome.objects.create(
            code='PO-1',
            description='Test program outcome description'
        )
        self.assertEqual(po.code, 'PO-1')
        self.assertEqual(po.description, 'Test program outcome description')
        self.assertIn('PO-1', str(po))
    
    def test_program_outcome_unique_code(self):
        """ProgramOutcome code unique olmalı"""
        ProgramOutcome.objects.create(code='PO-1', description='Test')
        with self.assertRaises(Exception):
            ProgramOutcome.objects.create(code='PO-1', description='Another')


class OutcomeWeightModelTest(TestCase):
    """OutcomeWeight model testleri"""
    
    def setUp(self):
        self.course = Course.objects.create(
            course_code='CSE311',
            course_name='Software Engineering'
        )
        self.component = EvaluationComponent.objects.create(
            course=self.course,
            name='Midterm',
            percentage=40
        )
        self.outcome = LearningOutcome.objects.create(
            course=self.course,
            description='Test outcome'
        )
    
    def test_outcome_weight_creation(self):
        """OutcomeWeight oluşturma testi"""
        weight = OutcomeWeight.objects.create(
            component=self.component,
            outcome=self.outcome,
            weight=3
        )
        self.assertEqual(weight.component, self.component)
        self.assertEqual(weight.outcome, self.outcome)
        self.assertEqual(weight.weight, 3)
    
    def test_outcome_weight_unique_together(self):
        """Aynı component-outcome çifti için sadece bir weight olabilir"""
        OutcomeWeight.objects.create(
            component=self.component,
            outcome=self.outcome,
            weight=3
        )
        with self.assertRaises(Exception):
            OutcomeWeight.objects.create(
                component=self.component,
                outcome=self.outcome,
                weight=5
            )

