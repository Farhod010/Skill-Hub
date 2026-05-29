from django.urls import reverse
from rest_framework.test import APITestCase

from accounts.models import User


class UserApiPermissionTests(APITestCase):
    def setUp(self):
        self.student = User.objects.create_user(
            email="student@example.com",
            password="StudentPass12345",
            username="student",
            role=User.Roles.STUDENT,
        )

    def test_student_cannot_promote_self_through_api(self):
        self.client.force_authenticate(self.student)
        response = self.client.patch(
            reverse("api:users-detail", args=[self.student.pk]),
            {"role": User.Roles.ADMIN},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.student.refresh_from_db()
        self.assertEqual(self.student.role, User.Roles.STUDENT)
        self.assertEqual(response.data["role"], User.Roles.STUDENT)
