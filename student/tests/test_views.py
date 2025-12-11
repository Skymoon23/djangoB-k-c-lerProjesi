from decimal import Decimal
from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.urls import reverse
from course_management.models import (
    Profile, Course, LearningOutcome, EvaluationComponent,
    Grade, OutcomeWeight, ProgramOutcome, LearningOutcomeProgramOutcomeWeight
)


class StudentDashboardTest(TestCase):
    """Student dashboard testleri"""
    
    def setUp(self):
        self.client = Client()
        self.student = User.objects.create_user(
            username='student',
            password='testpass123',
            first_name='Student',
            last_name='User'
        )
        profile, _ = Profile.objects.get_or_create(user=self.student)
        profile.role = 'student'
        profile.save()
        
        self.instructor = User.objects.create_user(
            username='instructor',
            password='testpass123'
        )
        profile, _ = Profile.objects.get_or_create(user=self.instructor)
        profile.role = 'instructor'
        profile.save()
        
        self.course = Course.objects.create(
            course_code='CSE311',
            course_name='Software Engineering'
        )
        self.course.instructors.add(self.instructor)
        self.course.students.add(self.student)
        
        self.component = EvaluationComponent.objects.create(
            course=self.course,
            name='Midterm',
            percentage=40
        )
        
        self.outcome = LearningOutcome.objects.create(
            course=self.course,
            description='Test Learning Outcome'
        )
        
        OutcomeWeight.objects.create(
            component=self.component,
            outcome=self.outcome,
            weight=3
        )
    
    def test_student_dashboard_access(self):
        """Öğrenci dashboard erişim testi"""
        self.client.login(username='student', password='testpass123')
        response = self.client.get(reverse('student_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'student/student_dashboard.html')
    
    def test_student_dashboard_without_login(self):
        """Login olmadan dashboard erişim testi"""
        response = self.client.get(reverse('student_dashboard'))
        self.assertEqual(response.status_code, 302)  # Login'e redirect
    
    def test_student_dashboard_course_list(self):
        """Dashboard'da ders listesi testi"""
        self.client.login(username='student', password='testpass123')
        response = self.client.get(reverse('student_dashboard'))
        self.assertContains(response, 'CSE311')
        self.assertContains(response, 'Software Engineering')
    
    def test_student_dashboard_grade_calculation(self):
        """Not hesaplama testi"""
        Grade.objects.create(
            student=self.student,
            component=self.component,
            score=Decimal('85.0')
        )
        
        self.client.login(username='student', password='testpass123')
        response = self.client.get(reverse('student_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('course_data', response.context)
        self.assertEqual(len(response.context['course_data']), 1)
        self.assertIsNotNone(response.context['course_data'][0]['final_grade'])
    
    def test_student_dashboard_no_courses(self):
        """Ders kayıtlı olmayan öğrenci için dashboard testi"""
        new_student = User.objects.create_user(
            username='newstudent',
            password='testpass123'
        )
        profile, _ = Profile.objects.get_or_create(user=new_student)
        profile.role = 'student'
        profile.save()
        
        self.client.login(username='newstudent', password='testpass123')
        response = self.client.get(reverse('student_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['course_data']), 0)
    
    def test_student_dashboard_learning_outcome_scores(self):
        """Learning outcome skorları hesaplama testi"""
        Grade.objects.create(
            student=self.student,
            component=self.component,
            score=Decimal('80.0')
        )
        
        self.client.login(username='student', password='testpass123')
        response = self.client.get(reverse('student_dashboard'))
        self.assertEqual(response.status_code, 200)
        course_data = response.context['course_data'][0]
        self.assertIn('learning_outcome_scores', course_data)
        self.assertEqual(len(course_data['learning_outcome_scores']), 1)


class StudentCourseDetailTest(TestCase):
    """Student course detail testleri"""
    
    def setUp(self):
        self.client = Client()
        self.student = User.objects.create_user(
            username='student',
            password='testpass123',
            first_name='Student',
            last_name='User'
        )
        profile, _ = Profile.objects.get_or_create(user=self.student)
        profile.role = 'student'
        profile.save()
        
        self.instructor = User.objects.create_user(
            username='instructor',
            password='testpass123'
        )
        profile, _ = Profile.objects.get_or_create(user=self.instructor)
        profile.role = 'instructor'
        profile.save()
        
        self.course = Course.objects.create(
            course_code='CSE311',
            course_name='Software Engineering'
        )
        self.course.instructors.add(self.instructor)
        self.course.students.add(self.student)
        
        self.component = EvaluationComponent.objects.create(
            course=self.course,
            name='Midterm',
            percentage=40
        )
        
        self.outcome = LearningOutcome.objects.create(
            course=self.course,
            description='Test Learning Outcome'
        )
        
        self.program_outcome = ProgramOutcome.objects.create(
            code='PO-1',
            description='Test Program Outcome'
        )
        
        OutcomeWeight.objects.create(
            component=self.component,
            outcome=self.outcome,
            weight=3
        )
        
        LearningOutcomeProgramOutcomeWeight.objects.create(
            learning_outcome=self.outcome,
            program_outcome=self.program_outcome,
            weight=4
        )
    
    def test_student_course_detail_access(self):
        """Öğrenci ders detay erişim testi"""
        self.client.login(username='student', password='testpass123')
        response = self.client.get(
            reverse('student_course_detail', args=[self.course.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'student/student_course_detail.html')
    
    def test_student_course_detail_without_login(self):
        """Login olmadan ders detay erişim testi"""
        response = self.client.get(
            reverse('student_course_detail', args=[self.course.id])
        )
        self.assertEqual(response.status_code, 302)  # Login'e redirect
    
    def test_student_course_detail_unauthorized_course(self):
        """Kayıtlı olmadığı derse erişim testi"""
        other_course = Course.objects.create(
            course_code='CSE312',
            course_name='Other Course'
        )
        
        self.client.login(username='student', password='testpass123')
        response = self.client.get(
            reverse('student_course_detail', args=[other_course.id])
        )
        self.assertEqual(response.status_code, 404)  # Not found
    
    def test_student_course_detail_grade_display(self):
        """Not gösterimi testi"""
        Grade.objects.create(
            student=self.student,
            component=self.component,
            score=Decimal('85.50')
        )
        
        self.client.login(username='student', password='testpass123')
        response = self.client.get(
            reverse('student_course_detail', args=[self.course.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('component_grade_list', response.context)
        self.assertEqual(len(response.context['component_grade_list']), 1)
    
    def test_student_course_detail_program_outcome_scores(self):
        """Program outcome skorları hesaplama testi"""
        Grade.objects.create(
            student=self.student,
            component=self.component,
            score=Decimal('80.0')
        )
        
        self.client.login(username='student', password='testpass123')
        response = self.client.get(
            reverse('student_course_detail', args=[self.course.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('program_outcome_scores', response.context)
        self.assertEqual(len(response.context['program_outcome_scores']), 1)

