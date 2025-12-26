from decimal import Decimal
from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.urls import reverse
from course_management.models import (
    Profile, Course, LearningOutcome, EvaluationComponent,
    Grade, OutcomeWeight, ProgramOutcome, LearningOutcomeProgramOutcomeWeight
)


class DepartmentHeadDashboardTest(TestCase):
    
    def setUp(self):
        self.client = Client()
        class_name = self.__class__.__name__.lower()
        self.department_head = User.objects.create_user(
            username=f'{class_name}_head',
            password='testpass123',
            first_name='Department',
            last_name='Head'
        )
        profile, _ = Profile.objects.get_or_create(user=self.department_head)
        profile.role = 'department_head'
        profile.save()
        
        self.instructor = User.objects.create_user(
            username=f'{class_name}_instructor',
            password='testpass123',
            first_name='Instructor',
            last_name='User'
        )
        profile, _ = Profile.objects.get_or_create(user=self.instructor)
        profile.role = 'instructor'
        profile.save()
        
        self.student = User.objects.create_user(
            username=f'{class_name}_student',
            password='testpass123',
            first_name='Student',
            last_name='User'
        )
        profile, _ = Profile.objects.get_or_create(user=self.student)
        profile.role = 'student'
        profile.save()
    
    def test_department_head_dashboard_access(self):
        self.client.login(username=self.department_head.username, password='testpass123')
        
        response = self.client.get(reverse('department_head_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'headteacher/department_head_dashboard.html')
    
    def test_create_program_outcome(self):
        self.client.login(username=self.department_head.username, password='testpass123')
        
        response = self.client.post(
            reverse('department_head_create_program_outcome'),
            {
                'code': 'PO-1',
                'description': 'Test program outcome'
            }
        )
        self.assertEqual(response.status_code, 302)
        
        self.assertTrue(
            ProgramOutcome.objects.filter(
                code='PO-1',
                description='Test program outcome'
            ).exists()
        )


class ManageLoPoWeightsTest(TestCase):
    
    def setUp(self):
        self.client = Client()
        class_name = self.__class__.__name__.lower()
        self.department_head = User.objects.create_user(
            username=f'{class_name}_head',
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
        self.client.login(username=self.department_head.username, password='testpass123')
        
        response = self.client.get(reverse('manage_lo_po_weights'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'headteacher/department_head_manage_lo_po_weights.html')
    
    def test_manage_weights_post(self):
        self.client.login(username=self.department_head.username, password='testpass123')
        
        response = self.client.post(
            reverse('manage_lo_po_weights'),
            {
                'outcome_id': self.outcome.id,
                f'weight_{self.outcome.id}_{self.program_outcome.id}': '3'
            }
        )
        self.assertEqual(response.status_code, 302)
        
        weight = LearningOutcomeProgramOutcomeWeight.objects.get(
            learning_outcome=self.outcome,
            program_outcome=self.program_outcome
        )
        self.assertEqual(weight.weight, 3)
        
        response = self.client.post(
            reverse('manage_lo_po_weights'),
            {
                'outcome_id': self.outcome.id,
                f'weight_{self.outcome.id}_{self.program_outcome.id}': '4'
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        
        weight.refresh_from_db()
        self.assertEqual(weight.weight, 4)


class ViewOutcomesTest(TestCase):
    def setUp(self):
        self.client = Client()
        class_name = self.__class__.__name__.lower()
        self.department_head = User.objects.create_user(
            username=f'{class_name}_head',
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
    
    def test_view_outcomes(self):
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
        
        self.client.login(username=self.department_head.username, password='testpass123')
        
        response = self.client.get(reverse('view_outcomes'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('course_data', response.context)
        self.assertEqual(len(response.context['course_data']), 1)


class POAchievementTest(TestCase):
    
    def setUp(self):
        self.client = Client()
        class_name = self.__class__.__name__.lower()
        self.department_head = User.objects.create_user(
            username=f'{class_name}_head',
            password='testpass123'
        )
        profile, _ = Profile.objects.get_or_create(user=self.department_head)
        profile.role = 'department_head'
        profile.save()
        
        self.student = User.objects.create_user(
            username=f'{class_name}_student',
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
    
    def test_program_outcome_achievement(self):
        self.client.login(username=self.department_head.username, password='testpass123')
        
        response = self.client.get(reverse('po_achievement'))
        self.assertEqual(response.status_code, 200)
        
        Grade.objects.create(
            student=self.student,
            component=self.component,
            score=Decimal('80.0')
        )
        
        response = self.client.get(reverse('po_achievement'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('po_achievement_data', response.context)
        self.assertEqual(len(response.context['po_achievement_data']), 1)


class EditProgramOutcomeTest(TestCase):
    
    def setUp(self):
        self.client = Client()
        class_name = self.__class__.__name__.lower()
        self.department_head = User.objects.create_user(
            username=f'{class_name}_head',
            password='testpass123'
        )
        profile, _ = Profile.objects.get_or_create(user=self.department_head)
        profile.role = 'department_head'
        profile.save()
        
        self.program_outcome = ProgramOutcome.objects.create(
            code='PO-1',
            description='Original description'
        )
    
    def test_edit_program_outcome(self):
        self.client.login(username=self.department_head.username, password='testpass123')
        
        response = self.client.get(
            reverse('edit_program_outcome', args=[self.program_outcome.id])
        )
        self.assertEqual(response.status_code, 200)
        
        response = self.client.post(
            reverse('edit_program_outcome', args=[self.program_outcome.id]),
            {'code': 'PO-1', 'description': 'Updated description'}
        )
        self.assertEqual(response.status_code, 302)
        
        self.program_outcome.refresh_from_db()
        self.assertEqual(self.program_outcome.description, 'Updated description')


class DeleteProgramOutcomeTest(TestCase):
    
    def setUp(self):
        self.client = Client()
        class_name = self.__class__.__name__.lower()
        self.department_head = User.objects.create_user(
            username=f'{class_name}_head',
            password='testpass123'
        )
        profile, _ = Profile.objects.get_or_create(user=self.department_head)
        profile.role = 'department_head'
        profile.save()
        
        self.program_outcome = ProgramOutcome.objects.create(
            code='PO-1',
            description='Test program outcome'
        )
    
    def test_delete_program_outcome(self):
        self.client.login(username=self.department_head.username, password='testpass123')
        
        response = self.client.post(
            reverse('delete_program_outcome', args=[self.program_outcome.id])
        )
        self.assertEqual(response.status_code, 302)
        
        self.assertFalse(
            ProgramOutcome.objects.filter(id=self.program_outcome.id).exists()
        )


class DepartmentHeadQuickActionsTest(TestCase):
    
    def setUp(self):
        self.client = Client()
        class_name = self.__class__.__name__.lower()
        self.department_head = User.objects.create_user(
            username=f'{class_name}_head',
            password='testpass123'
        )
        profile, _ = Profile.objects.get_or_create(user=self.department_head)
        profile.role = 'department_head'
        profile.save()
        
        self.instructor = User.objects.create_user(
            username=f'{class_name}_instructor',
            password='testpass123'
        )
        profile, _ = Profile.objects.get_or_create(user=self.instructor)
        profile.role = 'instructor'
        profile.save()
    
    def test_quick_actions(self):
        self.client.login(username=self.department_head.username, password='testpass123')
        
        response = self.client.get(reverse('department_head_quick_actions'))
        self.assertEqual(response.status_code, 200)
        
        response = self.client.post(
            reverse('department_head_quick_actions'),
            {'course_code': 'CSE311', 'course_name': 'Test', 'instructors': [self.instructor.id]}
        )
        self.assertEqual(response.status_code, 302)
        
        self.assertTrue(Course.objects.filter(course_code='CSE311').exists())


class DepartmentHeadListPagesTest(TestCase):
    
    def setUp(self):
        self.client = Client()
        class_name = self.__class__.__name__.lower()
        self.department_head = User.objects.create_user(
            username=f'{class_name}_head',
            password='testpass123'
        )
        profile, _ = Profile.objects.get_or_create(user=self.department_head)
        profile.role = 'department_head'
        profile.save()
    
    def test_list_pages(self):
        """Liste sayfaları erişim testleri"""
        self.client.login(username=self.department_head.username, password='testpass123')
        
        for url_name in ['department_head_outcomes_menu', 'department_head_courses',
                        'department_head_program_outcomes', 'department_head_instructors',
                        'department_head_students']:
            response = self.client.get(reverse(url_name))
            self.assertEqual(response.status_code, 200)


class EditInstructorCoursesTest(TestCase):
    
    def setUp(self):
        self.client = Client()
        class_name = self.__class__.__name__.lower()
        self.department_head = User.objects.create_user(
            username=f'{class_name}_head',
            password='testpass123'
        )
        profile, _ = Profile.objects.get_or_create(user=self.department_head)
        profile.role = 'department_head'
        profile.save()
        
        self.instructor = User.objects.create_user(
            username=f'{class_name}_instructor',
            password='testpass123'
        )
        profile, _ = Profile.objects.get_or_create(user=self.instructor)
        profile.role = 'instructor'
        profile.save()
        
        self.course = Course.objects.create(
            course_code='CSE311',
            course_name='Software Engineering'
        )
    
    def test_edit_instructor_courses_add(self):
        self.client.login(username=self.department_head.username, password='testpass123')
        
        response = self.client.post(
            reverse('edit_instructor_courses', args=[self.instructor.id]),
            {'action': 'add', 'course_id': self.course.id}
        )
        self.assertEqual(response.status_code, 302)
        
        self.assertIn(self.course, self.instructor.courses_taught.all())
    
    def test_edit_instructor_courses_remove(self):
        self.instructor.courses_taught.add(self.course)
        self.client.login(username=self.department_head.username, password='testpass123')
        
        response = self.client.post(
            reverse('edit_instructor_courses', args=[self.instructor.id]),
            {'action': 'remove', 'course_id': self.course.id}
        )
        self.assertEqual(response.status_code, 302)
        
        self.assertNotIn(self.course, self.instructor.courses_taught.all())


class EditStudentCoursesTest(TestCase):
    
    def setUp(self):
        self.client = Client()
        class_name = self.__class__.__name__.lower()
        self.department_head = User.objects.create_user(
            username=f'{class_name}_head',
            password='testpass123'
        )
        profile, _ = Profile.objects.get_or_create(user=self.department_head)
        profile.role = 'department_head'
        profile.save()
        
        self.student = User.objects.create_user(
            username=f'{class_name}_student',
            password='testpass123'
        )
        profile, _ = Profile.objects.get_or_create(user=self.student)
        profile.role = 'student'
        profile.save()
        
        self.course = Course.objects.create(
            course_code='CSE311',
            course_name='Software Engineering'
        )
    
    def test_edit_student_courses_add(self):
        self.client.login(username=self.department_head.username, password='testpass123')
        
        response = self.client.post(
            reverse('edit_student_courses', args=[self.student.id]),
            {'action': 'add', 'course_id': self.course.id}
        )
        self.assertEqual(response.status_code, 302)
        
        self.assertIn(self.course, self.student.enrolled_courses.all())
    
    def test_edit_student_courses_remove(self):
        self.student.enrolled_courses.add(self.course)
        self.client.login(username=self.department_head.username, password='testpass123')
        
        response = self.client.post(
            reverse('edit_student_courses', args=[self.student.id]),
            {'action': 'remove', 'course_id': self.course.id}
        )
        self.assertEqual(response.status_code, 302)
        
        self.assertNotIn(self.course, self.student.enrolled_courses.all())


class DeleteStudentTest(TestCase):
    
    def setUp(self):
        self.client = Client()
        class_name = self.__class__.__name__.lower()
        self.department_head = User.objects.create_user(
            username=f'{class_name}_head',
            password='testpass123'
        )
        profile, _ = Profile.objects.get_or_create(user=self.department_head)
        profile.role = 'department_head'
        profile.save()
        
        self.student = User.objects.create_user(
            username=f'{class_name}_student',
            password='testpass123'
        )
        profile, _ = Profile.objects.get_or_create(user=self.student)
        profile.role = 'student'
        profile.save()
    
    def test_delete_student(self):
        self.client.login(username=self.department_head.username, password='testpass123')
        student_id = self.student.id
        
        response = self.client.post(reverse('delete_student', args=[student_id]))
        self.assertEqual(response.status_code, 302)
        
        self.assertFalse(User.objects.filter(id=student_id).exists())


class EditCourseTest(TestCase):
    
    def setUp(self):
        self.client = Client()
        class_name = self.__class__.__name__.lower()
        self.department_head = User.objects.create_user(
            username=f'{class_name}_head',
            password='testpass123'
        )
        profile, _ = Profile.objects.get_or_create(user=self.department_head)
        profile.role = 'department_head'
        profile.save()
        
        self.instructor = User.objects.create_user(
            username=f'{class_name}_instructor',
            password='testpass123'
        )
        profile, _ = Profile.objects.get_or_create(user=self.instructor)
        profile.role = 'instructor'
        profile.save()
        
        self.course = Course.objects.create(
            course_code='CSE311',
            course_name='Software Engineering'
        )
    
    def test_edit_course(self):
        self.client.login(username=self.department_head.username, password='testpass123')
        
        response = self.client.get(reverse('edit_course', args=[self.course.id]))
        self.assertEqual(response.status_code, 200)
        
        response = self.client.post(
            reverse('edit_course', args=[self.course.id]),
            {'course_code': 'CSE312', 'course_name': 'Updated', 'instructors': [self.instructor.id]}
        )
        self.assertEqual(response.status_code, 302)
        
        self.course.refresh_from_db()
        self.assertEqual(self.course.course_code, 'CSE312')


class DeleteCourseTest(TestCase):
    
    def setUp(self):
        self.client = Client()
        class_name = self.__class__.__name__.lower()
        self.department_head = User.objects.create_user(
            username=f'{class_name}_head',
            password='testpass123'
        )
        profile, _ = Profile.objects.get_or_create(user=self.department_head)
        profile.role = 'department_head'
        profile.save()
        
        self.course = Course.objects.create(
            course_code='CSE311',
            course_name='Software Engineering'
        )
    
    def test_delete_course(self):
        self.client.login(username=self.department_head.username, password='testpass123')
        course_id = self.course.id
        
        response = self.client.post(reverse('delete_course', args=[course_id]))
        self.assertEqual(response.status_code, 302)
        
        self.assertFalse(Course.objects.filter(id=course_id).exists())


class EditLearningOutcomeTest(TestCase):
    
    def setUp(self):
        self.client = Client()
        class_name = self.__class__.__name__.lower()
        self.department_head = User.objects.create_user(
            username=f'{class_name}_head',
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
            description='Original'
        )
    
    def test_edit_learning_outcome(self):
        self.client.login(username=self.department_head.username, password='testpass123')
        
        response = self.client.get(reverse('edit_learning_outcome', args=[self.outcome.id]))
        self.assertEqual(response.status_code, 200)
        
        response = self.client.post(
            reverse('edit_learning_outcome', args=[self.outcome.id]),
            {'description': 'Updated'}
        )
        self.assertEqual(response.status_code, 302)
        
        self.outcome.refresh_from_db()
        self.assertEqual(self.outcome.description, 'Updated')


class DeleteLearningOutcomeTest(TestCase):
    
    def setUp(self):
        self.client = Client()
        class_name = self.__class__.__name__.lower()
        self.department_head = User.objects.create_user(
            username=f'{class_name}_head',
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
            description='Test'
        )
    
    def test_delete_learning_outcome(self):
        self.client.login(username=self.department_head.username, password='testpass123')
        outcome_id = self.outcome.id
        
        response = self.client.post(reverse('delete_learning_outcome', args=[outcome_id]))
        self.assertEqual(response.status_code, 302)
        
        self.assertFalse(LearningOutcome.objects.filter(id=outcome_id).exists())

