from django.contrib import messages
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django.views import View
from django.views.generic import CreateView

from .forms import CustomAuthenticationForm, CustomUserCreationForm


class RegisterView(CreateView):
    template_name = "accounts/register.html"
    form_class = CustomUserCreationForm
    success_url = reverse_lazy("accounts:login")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(request.user.home_url)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        messages.success(
            self.request,
            _("Your account has been created. You can log in and start learning."),
        )
        return super().form_valid(form)


class EmailLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = CustomAuthenticationForm
    redirect_authenticated_user = True

    def form_valid(self, form):
        messages.success(self.request, _("Welcome back to SkillHub."))
        return super().form_valid(form)

    def get_success_url(self):
        return self.get_redirect_url() or self.request.user.home_url


class EmailLogoutView(LogoutView):
    next_page = reverse_lazy("landing")


class RoleHomeRedirectView(View):
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("accounts:login")
        return redirect(request.user.home_url)
