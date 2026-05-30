from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm, UserCreationForm
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .models import TeacherProfile, User


class BaseStyledModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs.setdefault("class", "checkbox-input")
            elif isinstance(widget, forms.FileInput):
                widget.attrs.setdefault("class", "file-input")
            else:
                widget.attrs.setdefault("class", "input")


class TeacherProfileFieldsMixin(forms.Form):
    specialization = forms.CharField(label=_("Specialization"), max_length=180, required=False)
    experience = forms.CharField(label=_("Experience"), max_length=180, required=False)
    social_links = forms.CharField(
        label=_("Social links"),
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
        help_text=_("Share portfolio, Telegram, LinkedIn, Instagram or other useful profile links."),
    )

    def _apply_teacher_profile_initial(self):
        instance = getattr(self, "instance", None)
        if not getattr(instance, "pk", None):
            return
        try:
            profile = instance.teacher_profile
        except TeacherProfile.DoesNotExist:
            profile = None
        if not profile:
            return
        self.fields["specialization"].initial = profile.specialization
        self.fields["experience"].initial = profile.experience
        self.fields["social_links"].initial = profile.social_links

    def save_teacher_profile(self, user):
        profile, _created = TeacherProfile.objects.get_or_create(user=user)
        profile.specialization = self.cleaned_data.get("specialization", "")
        profile.experience = self.cleaned_data.get("experience", "")
        profile.social_links = self.cleaned_data.get("social_links", "")
        profile.save()
        return profile


def apply_widget_classes(form):
    for field in form.fields.values():
        widget = field.widget
        if isinstance(widget, forms.CheckboxInput):
            widget.attrs.setdefault("class", "checkbox-input")
        elif isinstance(widget, forms.FileInput):
            widget.attrs.setdefault("class", "file-input")
        else:
            widget.attrs.setdefault("class", "input")


class PanelActorGuardMixin:
    allowed_non_superuser_roles = (
        (User.Roles.STUDENT, _("Student")),
        (User.Roles.INSTRUCTOR, _("Instructor")),
    )

    def apply_actor_constraints(self, actor):
        self.actor = actor
        if actor and not actor.is_superuser:
            if "role" in self.fields:
                self.fields["role"].choices = self.allowed_non_superuser_roles
            if "is_staff" in self.fields:
                self.fields["is_staff"].disabled = True
                self.fields["is_staff"].help_text = _("Only a superuser can grant staff access.")

    def clean_role(self):
        role = self.cleaned_data["role"]
        actor = getattr(self, "actor", None)
        if actor and not actor.is_superuser and role not in {
            User.Roles.STUDENT,
            User.Roles.INSTRUCTOR,
        }:
            raise ValidationError(_("Only a superuser can assign moderator or admin roles."))
        return role

    def clean_is_staff(self):
        value = self.cleaned_data.get("is_staff", False)
        actor = getattr(self, "actor", None)
        if actor and not actor.is_superuser:
            return self.instance.is_staff if getattr(self.instance, "pk", None) else False
        return value


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = (
            "email",
            "username",
            "first_name",
            "last_name",
            "phone",
            "role",
            "avatar",
            "bio",
        )
        widgets = {
            "bio": forms.Textarea(attrs={"rows": 4, "class": "input"}),
        }
        labels = {
            "email": _("Email"),
            "username": _("Username"),
            "first_name": _("First name"),
            "last_name": _("Last name"),
            "phone": _("Phone number"),
            "role": _("Role"),
            "avatar": _("Avatar"),
            "bio": _("Bio"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if isinstance(field.widget, forms.FileInput):
                field.widget.attrs.setdefault("class", "file-input")
            elif name != "bio":
                field.widget.attrs.setdefault("class", "input")
        self.fields["password1"].widget.attrs.setdefault("class", "input")
        self.fields["password2"].widget.attrs.setdefault("class", "input")
        self.fields["role"].choices = (
            (User.Roles.STUDENT, _("Student")),
            (User.Roles.INSTRUCTOR, _("Teacher")),
        )

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = self.cleaned_data.get("role") or User.Roles.STUDENT
        if commit:
            user.save()
        return user


class CustomAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(
        label=_("Email address"),
        widget=forms.EmailInput(attrs={"class": "input", "autofocus": True}),
    )
    password = forms.CharField(
        label=_("Password"),
        strip=False,
        widget=forms.PasswordInput(attrs={"class": "input"}),
    )

    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        if user.is_blocked:
            raise ValidationError(
                _("This account has been blocked. Please contact support."),
                code="blocked",
            )


class UserPanelForm(PanelActorGuardMixin, BaseStyledModelForm):
    def __init__(self, *args, actor=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_actor_constraints(actor)

    class Meta:
        model = User
        fields = (
            "email",
            "username",
            "first_name",
            "last_name",
            "phone",
            "role",
            "avatar",
            "bio",
            "is_active",
            "is_staff",
            "is_blocked",
        )
        widgets = {
            "bio": forms.Textarea(attrs={"rows": 4, "class": "input"}),
        }
        labels = {
            "email": _("Email"),
            "username": _("Username"),
            "first_name": _("First name"),
            "last_name": _("Last name"),
            "phone": _("Phone number"),
            "role": _("Role"),
            "avatar": _("Avatar"),
            "bio": _("Bio"),
            "is_active": _("Active"),
            "is_staff": _("Staff"),
            "is_blocked": _("Blocked"),
        }


class UserPanelCreationForm(PanelActorGuardMixin, UserCreationForm):
    def __init__(self, *args, actor=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_actor_constraints(actor)
        apply_widget_classes(self)

    class Meta:
        model = User
        fields = (
            "email",
            "username",
            "first_name",
            "last_name",
            "phone",
            "role",
            "avatar",
            "bio",
            "is_active",
            "is_staff",
            "is_blocked",
        )
        widgets = {
            "bio": forms.Textarea(attrs={"rows": 4, "class": "input"}),
        }
        labels = {
            "email": _("Email"),
            "username": _("Username"),
            "first_name": _("First name"),
            "last_name": _("Last name"),
            "phone": _("Phone number"),
            "role": _("Role"),
            "avatar": _("Avatar"),
            "bio": _("Bio"),
            "is_active": _("Active"),
            "is_staff": _("Staff"),
            "is_blocked": _("Blocked"),
        }


class TeacherPanelForm(TeacherProfileFieldsMixin, UserPanelForm):
    class Meta(UserPanelForm.Meta):
        fields = (
            "email",
            "username",
            "first_name",
            "last_name",
            "phone",
            "avatar",
            "bio",
            "is_active",
            "is_blocked",
        )

    def __init__(self, *args, actor=None, **kwargs):
        super().__init__(*args, actor=actor, **kwargs)
        self._apply_teacher_profile_initial()
        apply_widget_classes(self)

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Roles.INSTRUCTOR
        if commit:
            user.save()
            self.save_teacher_profile(user)
        return user


class TeacherPanelCreationForm(TeacherProfileFieldsMixin, UserPanelCreationForm):
    class Meta(UserPanelCreationForm.Meta):
        fields = (
            "email",
            "username",
            "first_name",
            "last_name",
            "phone",
            "avatar",
            "bio",
            "is_active",
            "is_blocked",
        )

    def __init__(self, *args, actor=None, **kwargs):
        super().__init__(*args, actor=actor, **kwargs)
        self.fields.pop("role", None)
        self.fields.pop("is_staff", None)
        apply_widget_classes(self)

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Roles.INSTRUCTOR
        user.is_staff = False
        if commit:
            user.save()
            self.save_m2m()
            self.save_teacher_profile(user)
        return user


class TeacherProfileUpdateForm(TeacherProfileFieldsMixin, BaseStyledModelForm):
    class Meta:
        model = User
        fields = (
            "first_name",
            "last_name",
            "email",
            "username",
            "phone",
            "avatar",
            "bio",
        )
        widgets = {
            "bio": forms.Textarea(attrs={"rows": 4}),
        }
        labels = {
            "first_name": _("First name"),
            "last_name": _("Last name"),
            "email": _("Email"),
            "username": _("Username"),
            "phone": _("Phone number"),
            "avatar": _("Avatar"),
            "bio": _("Bio"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_teacher_profile_initial()
        apply_widget_classes(self)

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Roles.INSTRUCTOR
        if commit:
            user.save()
            self.save_teacher_profile(user)
        return user


class TeacherPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_widget_classes(self)
