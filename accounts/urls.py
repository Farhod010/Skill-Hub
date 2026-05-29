from django.urls import path

from .views import EmailLoginView, EmailLogoutView, RegisterView, RoleHomeRedirectView

app_name = "accounts"

urlpatterns = [
    path("home/", RoleHomeRedirectView.as_view(), name="home"),
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", EmailLoginView.as_view(), name="login"),
    path("logout/", EmailLogoutView.as_view(), name="logout"),
]
