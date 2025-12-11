from decimal import Decimal
from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.urls import reverse
from course_management.models import (
    Profile, Course, LearningOutcome, EvaluationComponent,
    Grade, OutcomeWeight
)


class InstructorDashboardTest(TestCase):
    """Instructor dashboard testleri"""
    
    def setUp(self):
        self.client = Client()
        self.instructor = User.objects.create_user(
            username='instructor',
            password='testpass123',
            first_name='Instructor',
            last_name='User'
        )
        profile, _ = Profile.objects.get_or_create(user=self.instructor)
        profile.role = 'instructor'
        profile.save()
        
        self.course = Course.objects.create(
            course_code='CSE311',
            course_name='Software Engineering'
        )
        self.course.instructors.add(self.instructor)
    
    def test_instructor_dashboard_access(self):
        """Öğretmen dashboard erişim testi"""
        self.client.login(username='instructor', password='testpass123')
        response = self.client.get(reverse('instructor_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'teacher/instructor_dashboard.html')
    
    def test_instructor_dashboard_without_login(self):
        """Login olmadan dashboard erişim testi"""
        response = self.client.get(reverse('instructor_dashboard'))
        self.assertEqual(response.status_code, 302)  # Login'e redirect
    
    def test_instructor_dashboard_course_list(self):
        """Dashboard'da ders listesi testi"""
        self.client.login(username='instructor', password='testpass123')
        response = self.client.get(reverse('instructor_dashboard'))
        self.assertContains(response, 'CSE311')
        self.assertContains(response, 'Software Engineering')
    
    def test_instructor_dashboard_only_own_courses(self):
        """Sadece kendi derslerini görmeli"""
        other_instructor = User.objects.create_user(
            username='otherinstructor',
            password='testpass123'
        )
        profile, _ = Profile.objects.get_or_create(user=other_instructor)
        profile.role = 'instructor'
        profile.save()
        
        other_course = Course.objects.create(
            course_code='CSE312',
            course_name='Other Course'
        )
        other_course.instructors.add(other_instructor)
        
        self.client.login(username='instructor', password='testpass123')
        response = self.client.get(reverse('instructor_dashboard'))
        self.assertContains(response, 'CSE311')
        self.assertNotContains(response, 'CSE312')


class ManageCourseTest(TestCase):
    """Manage course testleri"""
    
    def setUp(self):
        self.client = Client()
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
    
    def test_manage_course_access(self):
        """Ders yönetim sayfası erişim testi"""
        self.client.login(username='instructor', password='testpass123')
        response = self.client.get(
            reverse('manage_course', args=[self.course.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'teacher/course_manage_detail.html')
    
    def test_manage_course_unauthorized(self):
        """Yetkisiz ders yönetim erişim testi"""
        other_instructor = User.objects.create_user(
            username='otherinstructor',
            password='testpass123'
        )
        profile, _ = Profile.objects.get_or_create(user=other_instructor)
        profile.role = 'instructor'
        profile.save()
        
        self.client.login(username='otherinstructor', password='testpass123')
        response = self.client.get(
            reverse('manage_course', args=[self.course.id])
        )
        self.assertEqual(response.status_code, 404)  # Not found
    
    def test_add_evaluation_component(self):
        """Değerlendirme bileşeni ekleme testi"""
        self.client.login(username='instructor', password='testpass123')
        response = self.client.post(
            reverse('manage_course', args=[self.course.id]),
            {
                'submit_evaluation': '1',
                'name': 'Final',
                'percentage': 60
            }
        )
        self.assertEqual(response.status_code, 302)  # Redirect
        self.assertTrue(
            EvaluationComponent.objects.filter(
                course=self.course,
                name='Final',
                percentage=60
            ).exists()
        )
    
    def test_add_learning_outcome(self):
        """Learning outcome ekleme testi"""
        self.client.login(username='instructor', password='testpass123')
        response = self.client.post(
            reverse('manage_course', args=[self.course.id]),
            {
                'submit_outcome': '1',
                'description': 'Test learning outcome'
            }
        )
        self.assertEqual(response.status_code, 302)  # Redirect
        self.assertTrue(
            LearningOutcome.objects.filter(
                course=self.course,
                description='Test learning outcome'
            ).exists()
        )
    
    def test_submit_grades(self):
        """Not girme testi"""
        component = EvaluationComponent.objects.create(
            course=self.course,
            name='Midterm',
            percentage=40
        )
        
        self.client.login(username='instructor', password='testpass123')
        response = self.client.post(
            reverse('manage_course', args=[self.course.id]),
            {
                'submit_grades': '1',
                f'grade_{self.student.id}_{component.id}': '85.50'
            }
        )
        self.assertEqual(response.status_code, 302)  # Redirect
        grade = Grade.objects.get(
            student=self.student,
            component=component
        )
        self.assertEqual(grade.score, Decimal('85.50'))


class AddLearningOutcomeTest(TestCase):
    """Add learning outcome testleri"""
    
    def setUp(self):
        self.client = Client()
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
    
    def test_add_learning_outcome_get(self):
        """Learning outcome ekleme sayfası GET testi"""
        self.client.login(username='instructor', password='testpass123')
        response = self.client.get(
            reverse('add_learning_outcome', args=[self.course.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'teacher/add_learning_outcome.html')
    
    def test_add_learning_outcome_post(self):
        """Learning outcome ekleme POST testi"""
        self.client.login(username='instructor', password='testpass123')
        response = self.client.post(
            reverse('add_learning_outcome', args=[self.course.id]),
            {'description': 'Test learning outcome'}
        )
        self.assertEqual(response.status_code, 302)  # Redirect to dashboard
        self.assertTrue(
            LearningOutcome.objects.filter(
                course=self.course,
                description='Test learning outcome'
            ).exists()
        )


class ManageOutcomeWeightsTest(TestCase):
    """Manage outcome weights testleri"""
    
    def setUp(self):
        self.client = Client()
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
        
        self.component = EvaluationComponent.objects.create(
            course=self.course,
            name='Midterm',
            percentage=40
        )
        
        self.outcome = LearningOutcome.objects.create(
            course=self.course,
            description='Test outcome'
        )
    
    def test_manage_outcome_weights_get(self):
        """Outcome weights yönetim sayfası GET testi"""
        self.client.login(username='instructor', password='testpass123')
        response = self.client.get(
            reverse('manage_outcome_weights', args=[self.component.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'teacher/instructor_manage_outcomes.html')
    
    def test_manage_outcome_weights_post(self):
        """Outcome weights güncelleme POST testi"""
        self.client.login(username='instructor', password='testpass123')
        response = self.client.post(
            reverse('manage_outcome_weights', args=[self.component.id]),
            {f'weight_{self.outcome.id}': '4'}
        )
        self.assertEqual(response.status_code, 302)  # Redirect
        weight = OutcomeWeight.objects.get(
            component=self.component,
            outcome=self.outcome
        )
        self.assertEqual(weight.weight, 4)


class ManageComponentWeightsTest(TestCase):
    """Instructor manage component outcomes testleri"""
    
    def setUp(self):
        self.client = Client()
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
        
        self.component = EvaluationComponent.objects.create(
            course=self.course,
            name='Midterm',
            percentage=40
        )
        
        self.outcome = LearningOutcome.objects.create(
            course=self.course,
            description='Test outcome'
        )
    
    def test_manage_weights_get(self):
        """Component outcomes yönetim sayfası GET testi"""
        self.client.login(username='instructor', password='testpass123')
        response = self.client.get(reverse('manage_component_weights'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'teacher/instructor_manage_outcomes.html')
    
    def test_manage_weights_ajax_post(self):
        """AJAX ile outcome weights güncelleme testi"""
        self.client.login(username='instructor', password='testpass123')
        response = self.client.post(
            reverse('manage_component_weights'),
            {
                'component_id': self.component.id,
                f'weight_{self.component.id}_{self.outcome.id}': '5'
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content,
            {'success': True, 'message': 'Ağırlıklar başarıyla güncellendi.'}
        )
        weight = OutcomeWeight.objects.get(
            component=self.component,
            outcome=self.outcome
        )
        self.assertEqual(weight.weight, 5)

