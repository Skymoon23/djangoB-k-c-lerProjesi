from decimal import Decimal
from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.urls import reverse
from course_management.models import (
    Profile, Course, LearningOutcome, EvaluationComponent,
    Grade, OutcomeWeight
)


class TeacherViewsTest(TestCase):

    def setUp(self):
        self.client = Client()

        # Instructor
        self.instructor = User.objects.create_user(
            username="instructor",
            password="testpass123",
            first_name="Instructor",
            last_name="User"
        )
        profile, _ = Profile.objects.get_or_create(user=self.instructor)
        profile.role = "instructor"
        profile.save()

        # Student user
        self.student = User.objects.create_user(
            username="student1",
            password="testpass123",
            first_name="Student",
            last_name="User"
        )
        s_profile, _ = Profile.objects.get_or_create(user=self.student)
        s_profile.role = "student"
        s_profile.student_number = "220101"
        s_profile.save()

        # Course
        self.course = Course.objects.create(
            course_code="CSE101",
            course_name="Intro to Programming"
        )
        self.course.instructors.add(self.instructor)
        self.course.students.add(self.student)

        # Component
        self.component = EvaluationComponent.objects.create(
            course=self.course,
            name="Midterm",
            percentage=40
        )

        # Learning Outcome
        self.outcome = LearningOutcome.objects.create(
            course=self.course,
            description="Understand basics"
        )

        # Grade (DÜZELTİLDİ: User veriyoruz)
        Grade.objects.create(
            student=self.student,  # <-- hatanın sebebi buydu
            component=self.component,
            score=85
        )

    # -------------------- Tests ------------------------

    def test_instructor_dashboard(self):
        self.client.login(username="instructor", password="testpass123")
        response = self.client.get(reverse("instructor_dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "teacher/instructor_dashboard.html")
        self.assertContains(response, "CSE101")

    def test_manage_course_get(self):
        self.client.login(username="instructor", password="testpass123")
        response = self.client.get(
            reverse("manage_course", args=[self.course.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "teacher/course_manage_detail.html")

    def test_manage_course_add_evaluation_component(self):
        self.client.login(username="instructor", password="testpass123")
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
        self.client.login(username="instructor", password="testpass123")
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
        self.client.login(username="instructor", password="testpass123")
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

    def test_add_learning_outcome(self):
        self.client.login(username="instructor", password="testpass123")
        response = self.client.post(
            reverse("add_learning_outcome", args=[self.course.id]),
            {"description": "Test LO"}
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            LearningOutcome.objects.filter(description="Test LO").exists()
        )

    def test_manage_outcome_weights(self):
        self.client.login(username="instructor", password="testpass123")
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
        self.client.login(username="instructor", password="testpass123")
        response = self.client.post(
            reverse("manage_course_component_weights", args=[self.course.id]),
            {
                "component_id": self.component.id,
                f"weight_{self.component.id}_{self.outcome.id}": 4
            },
            HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )
        self.assertEqual(response.status_code, 200)
