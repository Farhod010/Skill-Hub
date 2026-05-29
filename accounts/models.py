from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from .managers import UserManager


class User(AbstractUser):
    class Roles(models.TextChoices):
        STUDENT = "student", _("Student")
        INSTRUCTOR = "instructor", _("Instructor")
        MODERATOR = "moderator", _("Moderator")
        ADMIN = "admin", _("Admin")

    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=30, blank=True)
    role = models.CharField(
        max_length=20,
        choices=Roles.choices,
        default=Roles.STUDENT,
    )
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
    bio = models.TextField(blank=True)
    is_blocked = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "first_name", "last_name"]

    objects = UserManager()

    class Meta:
        ordering = ["date_joined", "email"]

    def __str__(self):
        return self.email

    @property
    def full_name(self):
        return self.get_full_name() or self.username

    @property
    def can_access_panel(self):
        return self.is_authenticated and (
            self.is_superuser
            or self.is_staff
            or self.role in {self.Roles.ADMIN, self.Roles.MODERATOR}
        )

    @property
    def home_url(self):
        if self.can_access_panel:
            return reverse("panel:dashboard")
        if self.role == self.Roles.INSTRUCTOR:
            return reverse("dashboard:teacher_dashboard")
        return reverse("dashboard:student_dashboard")
