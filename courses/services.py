from decimal import Decimal

from payments.models import Payment

from .models import Certificate, Course, Enrollment, Lesson, QuizResult, WatchProgress


def user_has_course_access(user, course: Course) -> bool:
    if not getattr(user, "is_authenticated", False):
        return False
    if user.can_access_panel or course.instructor_id == user.id:
        return True
    return Enrollment.objects.filter(student=user, course=course).exists()


def enroll_user_in_course(
    user,
    course: Course,
    *,
    amount=None,
    provider: str | None = None,
):
    price_paid = course.final_price if amount is None else Decimal(amount)
    payment_provider = provider or ("free" if price_paid <= 0 else "demo")

    enrollment, created = Enrollment.objects.get_or_create(
        student=user,
        course=course,
        defaults={"price_paid": price_paid},
    )
    payment = None
    if created:
        payment = Payment.objects.create(
            user=user,
            course=course,
            enrollment=enrollment,
            amount=price_paid,
            provider=payment_provider,
            status=Payment.Status.COMPLETED,
        )
    return enrollment, payment, created


def student_completed_course(student, course: Course) -> bool:
    lesson_ids = list(
        Lesson.objects.filter(section__course=course).values_list("id", flat=True)
    )
    if not lesson_ids:
        return False
    completed_count = WatchProgress.objects.filter(
        student=student,
        lesson_id__in=lesson_ids,
        completed=True,
    ).count()
    return completed_count == len(lesson_ids)


def student_passed_course_quiz(student, course: Course):
    return (
        QuizResult.objects.filter(
            student=student,
            quiz__course=course,
            passed=True,
        )
        .select_related("quiz")
        .order_by("-submitted_at")
        .first()
    )


def issue_certificate_if_eligible(student, course: Course):
    if not course.certificate_enabled:
        return None
    if not student_completed_course(student, course):
        return None
    passed_quiz_result = student_passed_course_quiz(student, course)
    if course.quiz_count and not passed_quiz_result:
        return None
    certificate, _ = Certificate.objects.get_or_create(
        student=student,
        course=course,
        defaults={"quiz_result": passed_quiz_result},
    )
    if passed_quiz_result and certificate.quiz_result_id != passed_quiz_result.id:
        certificate.quiz_result = passed_quiz_result
        certificate.save(update_fields=["quiz_result"])
    return certificate
