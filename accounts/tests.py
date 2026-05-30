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


class LanguageSwitcherTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            email="panel-admin@example.com",
            password="AdminPass12345",
            username="paneladmin",
            role=User.Roles.ADMIN,
            is_staff=True,
        )

    def test_language_switcher_renders_translated_next_urls(self):
        self.client.force_login(self.admin)
        response = self.client.get("/en/panel/users/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'value="/ru/panel/users/"')
        self.assertContains(response, 'value="/uz/panel/users/"')

    def test_set_language_redirects_when_translated_next_is_posted(self):
        response = self.client.post(
            reverse("set_language"),
            {"language": "ru", "next": "/ru/panel/users/"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/ru/panel/users/")
        self.assertEqual(response.cookies["django_language"].value, "ru")

    def test_panel_page_renders_in_selected_language(self):
        self.client.force_login(self.admin)
        self.client.cookies["django_language"] = "ru"

        response = self.client.get("/ru/panel/users/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.wsgi_request.LANGUAGE_CODE, "ru")
        self.assertContains(response, "Пользователи")
