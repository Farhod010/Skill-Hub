from django.test import TestCase
from django.urls import reverse

from .models import User


class RoleRoutingTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            email="admin@example.com",
            password="AdminPass12345",
            username="admin",
            role=User.Roles.ADMIN,
            is_staff=True,
        )
        self.student = User.objects.create_user(
            email="student@example.com",
            password="StudentPass12345",
            username="student",
            role=User.Roles.STUDENT,
        )
        self.instructor = User.objects.create_user(
            email="teacher@example.com",
            password="TeacherPass12345",
            username="teacher",
            role=User.Roles.INSTRUCTOR,
        )

    def test_admin_home_redirects_to_panel(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("accounts:home"))
        self.assertRedirects(response, reverse("panel:dashboard"))

    def test_student_panel_redirects_to_dashboard(self):
        self.client.force_login(self.student)
        response = self.client.get(reverse("panel:dashboard"))
        self.assertRedirects(response, reverse("dashboard:student_dashboard"))

    def test_instructor_home_redirects_to_teacher_dashboard(self):
        self.client.force_login(self.instructor)
        response = self.client.get(reverse("accounts:home"))
        self.assertRedirects(response, reverse("dashboard:teacher_dashboard"))
