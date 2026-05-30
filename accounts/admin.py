from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .forms import CustomUserCreationForm
from .models import TeacherProfile, User


class TeacherProfileInline(admin.StackedInline):
    model = TeacherProfile
    extra = 0
    can_delete = False
    fields = ("specialization", "experience", "social_links")


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    add_form = CustomUserCreationForm
    model = User
    inlines = [TeacherProfileInline]
    list_display = (
        "email",
        "username",
        "role",
        "is_blocked",
        "is_staff",
        "is_active",
    )
    list_filter = ("role", "is_blocked", "is_staff", "is_superuser", "is_active")
    search_fields = ("email", "username", "first_name", "last_name")
    ordering = ("email",)
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            "Personal info",
            {"fields": ("username", "first_name", "last_name", "phone", "avatar", "bio")},
        ),
        ("Platform role", {"fields": ("role", "is_blocked")}),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "username",
                    "first_name",
                    "last_name",
                    "phone",
                    "role",
                    "password1",
                    "password2",
                    "is_staff",
                    "is_superuser",
                    "is_active",
                ),
            },
        ),
    )


@admin.register(TeacherProfile)
class TeacherProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "specialization", "experience")
    search_fields = ("user__email", "user__first_name", "user__last_name", "specialization", "experience")
