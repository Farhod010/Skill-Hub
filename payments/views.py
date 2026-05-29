from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext as _

from courses.models import Course
from courses.services import enroll_user_in_course, user_has_course_access

PAYMENT_METHODS = [
    ("click", "Click"),
    ("payme", "Payme"),
    ("uzum", "Uzum Bank"),
    ("card", _("Card payment")),
    ("demo", _("Demo payment")),
]


@login_required
def course_checkout(request, slug):
    course = get_object_or_404(
        Course.objects.select_related("category", "instructor"),
        slug=slug,
        is_published=True,
    )

    if user_has_course_access(request.user, course):
        messages.info(request, _("You already have access to this course."))
        return redirect(course.get_absolute_url())

    if course.is_free:
        messages.info(request, _("This course is free. Enroll directly to start learning."))
        return redirect(course.get_absolute_url())

    if request.method == "POST":
        provider = request.POST.get("provider") or "demo"
        enrollment, payment, created = enroll_user_in_course(
            request.user,
            course,
            amount=course.final_price,
            provider=provider,
        )
        if created:
            messages.success(
                request,
                _("%(course)s is now unlocked for you.") % {"course": course.get_translated_title()},
            )
        else:
            messages.info(request, _("You are already enrolled in this course."))
        if course.first_lesson:
            return redirect(course.first_lesson.get_absolute_url())
        return redirect(course.get_absolute_url())

    return render(
        request,
        "payments/checkout.html",
        {
            "course": course,
            "preview_lesson_count": course.preview_lesson_count,
            "payment_methods": PAYMENT_METHODS,
        },
    )
