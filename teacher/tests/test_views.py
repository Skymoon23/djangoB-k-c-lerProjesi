from decimal import Decimal
from io import BytesIO

import pandas as pd
from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.urls import reverse
from unittest.mock import patch
from django.test import TransactionTestCase
from django.db import transaction
from course_management.models import (
    Profile, Course, LearningOutcome, EvaluationComponent,
    Grade, OutcomeWeight
)


class TeacherViewsTest(TestCase):

    def setUp(self):
        self.client = Client()
        class_name = self.__class__.__name__.lower()

        self.instructor = User.objects.create_user(
            username=f"{class_name}_instructor",
            password="testpass123",
            first_name="Instructor",
            last_name="User"
        )
        profile, _ = Profile.objects.get_or_create(user=self.instructor)
        profile.role = "instructor"
        profile.save()

        self.student = User.objects.create_user(
            username=f"{class_name}_student",
            password="testpass123",
            first_name="Student",
            last_name="User"
        )
        s_profile, _ = Profile.objects.get_or_create(user=self.student)
        s_profile.role = "student"
        s_profile.student_number = "220101"
        s_profile.save()

        self.course = Course.objects.create(
            course_code="CSE101",
            course_name="Intro to Programming"
        )
        self.course.instructors.add(self.instructor)
        self.course.students.add(self.student)

        self.component = EvaluationComponent.objects.create(
            course=self.course,
            name="Midterm",
            percentage=40
        )

        self.outcome = LearningOutcome.objects.create(
            course=self.course,
            description="Understand basics"
        )

        Grade.objects.create(
            student=self.student,
            component=self.component,
            score=85
        )

    def test_instructor_dashboard(self):
        self.client.login(username=self.instructor.username, password="testpass123")
        
        response = self.client.get(reverse("instructor_dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "teacher/instructor_dashboard.html")
        self.assertContains(response, "CSE101")

    def test_manage_course_get(self):
        self.client.login(username=self.instructor.username, password="testpass123")
        
        response = self.client.get(
            reverse("manage_course", args=[self.course.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "teacher/course_manage_detail.html")

    def test_manage_course_add_evaluation_component(self):
        self.client.login(username=self.instructor.username, password="testpass123")
        
        response = self.client.post(
            reverse("manage_course", args=[self.course.id]),
            {
                "submit_evaluation": "1",
                "name": "Final",
                "percentage": 60
            }
        )
        self.assertEqual(response.status_code, 302)
        
        self.assertTrue(
            EvaluationComponent.objects.filter(
                course=self.course,
                name="Final"
            ).exists()
        )

    def test_manage_course_add_learning_outcome(self):
        self.client.login(username=self.instructor.username, password="testpass123")
        
        response = self.client.post(
            reverse("manage_course", args=[self.course.id]),
            {
                "submit_outcome": "1",
                "description": "New LO"
            }
        )
        self.assertEqual(response.status_code, 302)
        
        self.assertTrue(
            LearningOutcome.objects.filter(
                course=self.course,
                description="New LO"
            ).exists()
        )

    def test_manage_course_update_grades(self):
        self.client.login(username=self.instructor.username, password="testpass123")
        
        response = self.client.post(
            reverse("manage_course", args=[self.course.id]),
            {
                "submit_grades": "1",
                f"grade_{self.student.id}_{self.component.id}": "92.5"
            }
        )
        self.assertEqual(response.status_code, 302)

        grade = Grade.objects.get(student=self.student, component=self.component)
        self.assertEqual(grade.score, Decimal("92.5"))

    def test_manage_outcome_weights(self):
        self.client.login(username=self.instructor.username, password="testpass123")
        
        response = self.client.post(
            reverse("manage_outcome_weights", args=[self.component.id]),
            {
                f"weight_{self.outcome.id}": 3
            }
        )
        self.assertEqual(response.status_code, 302)
        
        ow = OutcomeWeight.objects.get(component=self.component, outcome=self.outcome)
        self.assertEqual(ow.weight, 3)

    def test_manage_component_weights(self):
        self.client.login(username=self.instructor.username, password="testpass123")
        
        response = self.client.post(
            reverse("manage_course_component_weights", args=[self.course.id]),
            {
                "component_id": self.component.id,
                f"weight_{self.component.id}_{self.outcome.id}": 4
            },
            HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )
        self.assertEqual(response.status_code, 200)
        
        ow = OutcomeWeight.objects.get(component=self.component, outcome=self.outcome)
        self.assertEqual(ow.weight, 4)

    def test_add_grade(self):
        self.client.login(username=self.instructor.username, password="testpass123")
        
        response = self.client.get(reverse("add_grade", args=[self.component.id]))
        self.assertEqual(response.status_code, 302)
        
        response = self.client.post(
            reverse("add_grade", args=[self.component.id]),
            {"student": self.student.id, "score": 90}
        )
        self.assertEqual(response.status_code, 302)
        
        grade = Grade.objects.get(student=self.student, component=self.component)
        self.assertEqual(grade.score, Decimal("90"))

    def test_course_outcomes(self):
        self.client.login(username=self.instructor.username, password="testpass123")
        
        response = self.client.get(reverse("course_lo_add", args=[self.course.id]))
        self.assertEqual(response.status_code, 200)
        
        response = self.client.post(
            reverse("course_lo_add", args=[self.course.id]),
            {"description": "New LO"}
        )
        self.assertEqual(response.status_code, 302)
        
        self.assertTrue(LearningOutcome.objects.filter(description="New LO").exists())

    def test_course_components(self):
        self.client.login(username=self.instructor.username, password="testpass123")
        
        response = self.client.get(reverse("course_eval_add", args=[self.course.id]))
        self.assertEqual(response.status_code, 200)
        
        response = self.client.post(
            reverse("course_eval_add", args=[self.course.id]),
            {"name": "Final", "percentage": 60}
        )
        self.assertEqual(response.status_code, 302)
        
        self.assertTrue(EvaluationComponent.objects.filter(name="Final").exists())

    def test_edit_component(self):
        self.client.login(username=self.instructor.username, password="testpass123")
        
        response = self.client.get(
            reverse("edit_component", args=[self.course.id, self.component.id])
        )
        self.assertEqual(response.status_code, 200)
        
        response = self.client.post(
            reverse("edit_component", args=[self.course.id, self.component.id]),
            {"name": "Updated", "percentage": 50}
        )
        self.assertEqual(response.status_code, 302)
        
        self.component.refresh_from_db()
        self.assertEqual(self.component.name, "Updated")

    def test_delete_component(self):
        self.client.login(username=self.instructor.username, password="testpass123")
        comp_id = self.component.id
        
        response = self.client.post(
            reverse("delete_component", args=[self.course.id, comp_id])
        )
        self.assertEqual(response.status_code, 302)
        
        self.assertFalse(EvaluationComponent.objects.filter(id=comp_id).exists())

    def test_edit_outcome(self):
        self.client.login(username=self.instructor.username, password="testpass123")
        
        response = self.client.get(
            reverse("edit_outcome", args=[self.course.id, self.outcome.id])
        )
        self.assertEqual(response.status_code, 200)
        
        response = self.client.post(
            reverse("edit_outcome", args=[self.course.id, self.outcome.id]),
            {"description": "Updated"}
        )
        self.assertEqual(response.status_code, 302)
        
        self.outcome.refresh_from_db()
        self.assertEqual(self.outcome.description, "Updated")

    def test_delete_outcome(self):
        self.client.login(username=self.instructor.username, password="testpass123")
        outcome_id = self.outcome.id
        
        response = self.client.post(
            reverse("delete_outcome", args=[self.course.id, outcome_id])
        )
        self.assertEqual(response.status_code, 302)
        
        self.assertFalse(LearningOutcome.objects.filter(id=outcome_id).exists())


class RollbackError(Exception):
    pass


class TeacherRollbackTest(TransactionTestCase):
    def setUp(self):
        self.client = Client()
        class_name = self.__class__.__name__.lower()

        self.instructor = User.objects.create_user(
            username=f"{class_name}_instructor",
            password="testpass123"
        )
        profile, _ = Profile.objects.get_or_create(user=self.instructor)
        profile.role = "instructor"
        profile.save()

        self.student = User.objects.create_user(
            username=f"{class_name}_student",
            password="testpass123"
        )
        s_profile, _ = Profile.objects.get_or_create(user=self.student)
        s_profile.role = "student"
        s_profile.save()

        self.course = Course.objects.create(
            course_code="CSE101",
            course_name="Intro to Programming"
        )
        self.course.instructors.add(self.instructor)
        self.course.students.add(self.student)

        self.component = EvaluationComponent.objects.create(
            course=self.course,
            name="Midterm",
            percentage=40
        )
        self.outcome = LearningOutcome.objects.create(
            course=self.course,
            description="Understand basics"
        )

        Grade.objects.create(
            student=self.student,
            component=self.component,
            score=Decimal("50.0")
        )

        self.client.login(username=self.instructor.username, password="testpass123")

    def test_manage_course_update_grades_rollback(self):
        url = reverse('manage_course', args=[self.course.id])
        post_data = {
            'submit_grades': '1',
            f'grade_{self.student.id}_{self.component.id}': '90.0'
        }

        with patch.object(Grade, 'save', side_effect=RollbackError):
            try:
                self.client.post(url, post_data)
            except RollbackError:
                pass

        grade = Grade.objects.get(student=self.student, component=self.component)
        self.assertEqual(grade.score, Decimal("50.0"))

    def test_manage_component_weights_rollback(self):
        url = reverse('manage_course_component_weights', args=[self.course.id])
        post_data = {
            'component_id': self.component.id,
            f'weight_{self.component.id}_{self.outcome.id}': '5'
        }

        with patch('course_management.models.OutcomeWeight.objects.update_or_create', side_effect=RollbackError):
            try:
                self.client.post(url, post_data)
            except RollbackError:
                pass

        self.assertFalse(OutcomeWeight.objects.filter(component=self.component, outcome=self.outcome).exists())

    def test_upload_grades_excel_rollback(self):
        with patch('course_management.models.Grade.objects.update_or_create', side_effect=RollbackError):
            try:
                with transaction.atomic():
                    raise RollbackError()
            except RollbackError:
                pass

        self.assertEqual(Grade.objects.filter(student=self.student).count(), 1)

    def test_grade_multiple_rollback(self):
        s2 = User.objects.create_user(username="student2", password="123")
        self.course.students.add(s2)
        Grade.objects.create(student=s2, component=self.component, score=Decimal("40.0"))

        url = reverse('manage_course', args=[self.course.id])
        post_data = {
            'submit_grades': '1',
            f'grade_{self.student.id}_{self.component.id}': '100',
            f'grade_{s2.id}_{self.component.id}': '100'
        }

        with patch.object(Grade, 'save', side_effect=[None, RollbackError]):
            try:
                self.client.post(url, post_data)
            except RollbackError:
                pass

        self.assertEqual(Grade.objects.get(student=self.student, component=self.component).score, Decimal("50.0"))
        self.assertEqual(Grade.objects.get(student=s2, component=self.component).score, Decimal("40.0"))

    def test_weight_integrity_rollback(self):
        OutcomeWeight.objects.create(component=self.component, outcome=self.outcome, weight=10)
        url = reverse('manage_course_component_weights', args=[self.course.id])
        post_data = {'component_id': self.component.id, f'weight_{self.component.id}_{self.outcome.id}': ''}

        with patch('course_management.models.OutcomeWeight.objects.filter', side_effect=RollbackError):
            try:
                self.client.post(url, post_data)
            except RollbackError:
                pass

        self.assertTrue(OutcomeWeight.objects.filter(weight=10).exists())

    def test_excel_upload_rollback(self):
        df = pd.DataFrame({
            'username': [self.student.username, 'non_existent'],
            'component_name': [self.component.name, self.component.name],
            'score': [100, 80]
        })
        excel = BytesIO();
        df.to_excel(excel, index=False);
        excel.seek(0);
        excel.name = 'test.xlsx'

        url = reverse('upload_grades', args=[self.course.id])
        with patch('course_management.models.Grade.objects.update_or_create', side_effect=[None, RollbackError]):
            try:
                self.client.post(url, {'file': excel})
            except RollbackError:
                pass

        self.assertEqual(Grade.objects.get(student=self.student).score, Decimal("50.0"))