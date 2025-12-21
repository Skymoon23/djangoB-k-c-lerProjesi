from decimal import Decimal
from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.urls import reverse
from course_management.models import (
    Profile, Course, LearningOutcome, EvaluationComponent,
    Grade, OutcomeWeight, ProgramOutcome, LearningOutcomeProgramOutcomeWeight
)


class DepartmentHeadDashboardTest(TestCase):
    """Department head dashboard testleri"""
    
    def setUp(self):
        self.client = Client()
        self.department_head = User.objects.create_user(
            username='head',
            password='testpass123',
            first_name='Department',
            last_name='Head'
        )
        profile, _ = Profile.objects.get_or_create(user=self.department_head)
        profile.role = 'department_head'
        profile.save()
        
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
    
    def test_department_head_dashboard_access(self):
        """Bölüm başkanı dashboard erişim testi"""
        self.client.login(username='head', password='testpass123')
        response = self.client.get(reverse('department_head_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'headteacher/department_head_dashboard.html')
    
    def test_department_head_dashboard_without_login(self):
        """Login olmadan dashboard erişim testi"""
        response = self.client.get(reverse('department_head_dashboard'))
        self.assertEqual(response.status_code, 302)  # Login'e redirect   
           
    def test_create_program_outcome(self):
        """Program outcome oluşturma testi"""
        self.client.login(username='head', password='testpass123')
        response = self.client.post(
            reverse('department_head_create_program_outcome'),
            {
                'code': 'PO-1',
                'description': 'Test program outcome'
            }
        )
        self.assertEqual(response.status_code, 302)  # Redirect
        self.assertTrue(
            ProgramOutcome.objects.filter(
                code='PO-1',
                description='Test program outcome'
            ).exists()
        )


class ManageLoPoWeightsTest(TestCase):
    """Department head manage LO-PO weights testleri"""
    
    def setUp(self):
        self.client = Client()
        self.department_head = User.objects.create_user(
            username='head',
            password='testpass123'
        )
        profile, _ = Profile.objects.get_or_create(user=self.department_head)
        profile.role = 'department_head'
        profile.save()
        
        self.course = Course.objects.create(
            course_code='CSE311',
            course_name='Software Engineering'
        )
        
        self.outcome = LearningOutcome.objects.create(
            course=self.course,
            description='Test learning outcome'
        )
        
        self.program_outcome = ProgramOutcome.objects.create(
            code='PO-1',
            description='Test program outcome'
        )
    
    def test_manage_weights_get(self):
        """LO-PO weights yönetim sayfası GET testi"""
        self.client.login(username='head', password='testpass123')
        response = self.client.get(reverse('manage_lo_po_weights'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'headteacher/department_head_manage_lo_po_weights.html')
    
    def test_manage_weights_ajax_post(self):
        """AJAX ile LO-PO weights güncelleme testi"""
        self.client.login(username='head', password='testpass123')
        response = self.client.post(
            reverse('manage_lo_po_weights'),
            {
                'outcome_id': self.outcome.id,
                f'weight_{self.outcome.id}_{self.program_outcome.id}': '4'
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content,
            {'success': True, 'message': 'Ağırlıklar başarıyla güncellendi.'}
        )
        weight = LearningOutcomeProgramOutcomeWeight.objects.get(
            learning_outcome=self.outcome,
            program_outcome=self.program_outcome
        )
        self.assertEqual(weight.weight, 4)
    
    def test_manage_weights_normal_post(self):
        """Normal POST ile LO-PO weights güncelleme testi"""
        self.client.login(username='head', password='testpass123')
        response = self.client.post(
            reverse('manage_lo_po_weights'),
            {
                'outcome_id': self.outcome.id,
                f'weight_{self.outcome.id}_{self.program_outcome.id}': '3'
            }
        )
        self.assertEqual(response.status_code, 302)  # Redirect
        weight = LearningOutcomeProgramOutcomeWeight.objects.get(
            learning_outcome=self.outcome,
            program_outcome=self.program_outcome
        )
        self.assertEqual(weight.weight, 3)


class ViewOutcomesTest(TestCase):
    """Department head view outcomes testleri"""
    
    def setUp(self):
        self.client = Client()
        self.department_head = User.objects.create_user(
            username='head',
            password='testpass123'
        )
        profile, _ = Profile.objects.get_or_create(user=self.department_head)
        profile.role = 'department_head'
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
        
        self.outcome = LearningOutcome.objects.create(
            course=self.course,
            description='Test learning outcome'
        )
        
        self.program_outcome = ProgramOutcome.objects.create(
            code='PO-1',
            description='Test program outcome'
        )
    
    def test_view_outcomes_access(self):
        """Outcomes görüntüleme sayfası erişim testi"""
        self.client.login(username='head', password='testpass123')
        response = self.client.get(reverse('view_outcomes'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'headteacher/department_head_view_outcomes.html')
    
    def test_view_outcomes_displays_data(self):
        """Outcomes sayfasında veri gösterimi testi"""
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
        
        self.client.login(username='head', password='testpass123')
        response = self.client.get(reverse('view_outcomes'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('course_data', response.context)
        self.assertEqual(len(response.context['course_data']), 1)


class POAchievementTest(TestCase):
    """Department head program outcome achievement testleri"""
    
    def setUp(self):
        self.client = Client()
        self.department_head = User.objects.create_user(
            username='head',
            password='testpass123'
        )
        profile, _ = Profile.objects.get_or_create(user=self.department_head)
        profile.role = 'department_head'
        profile.save()
        
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
        self.course.students.add(self.student)
        
        self.component = EvaluationComponent.objects.create(
            course=self.course,
            name='Midterm',
            percentage=40
        )
        
        self.outcome = LearningOutcome.objects.create(
            course=self.course,
            description='Test learning outcome'
        )
        
        self.program_outcome = ProgramOutcome.objects.create(
            code='PO-1',
            description='Test program outcome'
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
    
    def test_program_outcome_achievement_access(self):
        """Program outcome achievement sayfası erişim testi"""
        self.client.login(username='head', password='testpass123')
        response = self.client.get(reverse('po_achievement'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'headteacher/department_head_program_outcome_achievement.html')
    
    def test_program_outcome_achievement_with_grades(self):
        """Notlarla program outcome achievement hesaplama testi"""
        Grade.objects.create(
            student=self.student,
            component=self.component,
            score=Decimal('80.0')
        )
        
        self.client.login(username='head', password='testpass123')
        response = self.client.get(reverse('po_achievement'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('po_achievement_data', response.context)
        self.assertEqual(len(response.context['po_achievement_data']), 1)


class EditProgramOutcomeTest(TestCase):
    """Edit program outcome testleri"""
    
    def setUp(self):
        self.client = Client()
        self.department_head = User.objects.create_user(
            username='head',
            password='testpass123'
        )
        profile, _ = Profile.objects.get_or_create(user=self.department_head)
        profile.role = 'department_head'
        profile.save()
        
        self.program_outcome = ProgramOutcome.objects.create(
            code='PO-1',
            description='Original description'
        )
    
    def test_edit_program_outcome_get(self):
        """Program outcome düzenleme sayfası GET testi"""
        self.client.login(username='head', password='testpass123')
        response = self.client.get(
            reverse('edit_program_outcome', args=[self.program_outcome.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'headteacher/edit_program_outcome.html')
    
    def test_edit_program_outcome_post(self):
        """Program outcome güncelleme POST testi"""
        self.client.login(username='head', password='testpass123')
        response = self.client.post(
            reverse('edit_program_outcome', args=[self.program_outcome.id]),
            {
                'code': 'PO-1',
                'description': 'Updated description'
            }
        )
        self.assertEqual(response.status_code, 302)  # Redirect
        self.program_outcome.refresh_from_db()
        self.assertEqual(self.program_outcome.description, 'Updated description')


class DeleteProgramOutcomeTest(TestCase):
    """Delete program outcome testleri"""
    
    def setUp(self):
        self.client = Client()
        self.department_head = User.objects.create_user(
            username='head',
            password='testpass123'
        )
        profile, _ = Profile.objects.get_or_create(user=self.department_head)
        profile.role = 'department_head'
        profile.save()
        
        self.program_outcome = ProgramOutcome.objects.create(
            code='PO-1',
            description='Test program outcome'
        )
    
    def test_delete_program_outcome_post(self):
        """Program outcome silme POST testi"""
        self.client.login(username='head', password='testpass123')
        response = self.client.post(
            reverse('delete_program_outcome', args=[self.program_outcome.id])
        )
        self.assertEqual(response.status_code, 302)  # Redirect
        self.assertFalse(
            ProgramOutcome.objects.filter(id=self.program_outcome.id).exists()
        )

