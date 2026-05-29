from django.urls import path

from .views import course_checkout

app_name = "payments"

urlpatterns = [
    path("checkout/<slug:slug>/", course_checkout, name="course_checkout"),
]
