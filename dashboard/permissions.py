from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.utils.translation import gettext as _

from accounts.models import User


def panel_access_required(view_func):
    @login_required
    @wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        if not request.user.can_access_panel:
            messages.info(request, _("Your account does not have access to the SkillHub panel."))
            return redirect(request.user.home_url)
        return view_func(request, *args, **kwargs)

    return wrapped_view


class PanelAccessMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.can_access_panel

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            messages.info(
                self.request,
                _("Your account does not have access to the SkillHub panel."),
            )
            return redirect(self.request.user.home_url)
        raise PermissionDenied(_("Authentication is required."))


def admin_required(view_func):
    @login_required
    @wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        if not request.user.can_access_panel:
            messages.info(request, _("Only platform admins can access this area."))
            return redirect(request.user.home_url)
        return view_func(request, *args, **kwargs)

    return wrapped_view


def teacher_required(view_func):
    @login_required
    @wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        if request.user.role != User.Roles.INSTRUCTOR:
            messages.info(request, _("Only instructors can access the teacher workspace."))
            return redirect(request.user.home_url)
        return view_func(request, *args, **kwargs)

    return wrapped_view


def student_required(view_func):
    @login_required
    @wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        if request.user.role != User.Roles.STUDENT:
            messages.info(request, _("Only students can access this area."))
            return redirect(request.user.home_url)
        return view_func(request, *args, **kwargs)

    return wrapped_view


def course_owner_required(model, lookup_kwarg="pk", field_name="pk", instructor_lookup="instructor"):
    def decorator(view_func):
        @login_required
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            if request.user.can_access_panel:
                return view_func(request, *args, **kwargs)
            if request.user.role != User.Roles.INSTRUCTOR:
                raise PermissionDenied(_("You do not have permission to access this resource."))
            lookup_value = kwargs.get(lookup_kwarg)
            filter_kwargs = {field_name: lookup_value, instructor_lookup: request.user}
            if not model.objects.filter(**filter_kwargs).exists():
                raise PermissionDenied(_("You do not have permission to manage this content."))
            return view_func(request, *args, **kwargs)

        return wrapped_view

    return decorator
