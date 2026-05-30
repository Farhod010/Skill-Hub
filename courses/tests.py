from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils.translation import override

from accounts.models import User
from payments.models import Payment

from .models import Answer, Category, Certificate, Course, Enrollment, Lesson, Question, Quiz, QuizResult, Review, Section


class EnrollmentAndLessonAccessTests(TestCase):
    def setUp(self):
        self.student = User.objects.create_user(
            email="student@example.com",
            password="StudentPass12345",
            username="student",
            role=User.Roles.STUDENT,
        )
        self.instructor = User.objects.create_user(
            email="instructor@example.com",
            password="InstructorPass12345",
            username="instructor",
            role=User.Roles.INSTRUCTOR,
        )
        self.other_instructor = User.objects.create_user(
            email="other-instructor@example.com",
            password="InstructorPass12345",
            username="otherinstructor",
            role=User.Roles.INSTRUCTOR,
        )
        self.admin = User.objects.create_user(
            email="admin@example.com",
            password="AdminPass12345",
            username="admin",
            role=User.Roles.ADMIN,
            is_staff=True,
        )
        self.category = Category.objects.create(title="Testing", description="Testing category")

        self.free_course = Course.objects.create(
            title="Free Course",
            category=self.category,
            instructor=self.instructor,
            short_description="Free course",
            full_description="Free course description",
            price=Decimal("0.00"),
            level=Course.Levels.BEGINNER,
            language="English",
            is_published=True,
        )
        free_section = Section.objects.create(course=self.free_course, title="Free section", order_index=1)
        self.free_lesson = Lesson.objects.create(
            section=free_section,
            title="Free lesson",
            order_index=1,
            duration_minutes=5,
            is_preview=False,
            video_url="https://samplelib.com/lib/preview/mp4/sample-5s.mp4",
        )

        self.paid_course = Course.objects.create(
            title="Paid Course",
            category=self.category,
            instructor=self.instructor,
            short_description="Paid course",
            full_description="Paid course description",
            price=Decimal("49.00"),
            level=Course.Levels.BEGINNER,
            language="English",
            is_published=True,
        )
        paid_section = Section.objects.create(course=self.paid_course, title="Paid section", order_index=1)
        self.preview_lesson = Lesson.objects.create(
            section=paid_section,
            title="Preview lesson",
            order_index=1,
            duration_minutes=5,
            is_preview=True,
            video_url="https://samplelib.com/lib/preview/mp4/sample-5s.mp4",
        )
        self.locked_lesson = Lesson.objects.create(
            section=paid_section,
            title="Locked lesson",
            order_index=2,
            duration_minutes=10,
            is_preview=False,
            video_url="https://samplelib.com/lib/preview/mp4/sample-10s.mp4",
        )
        self.other_course = Course.objects.create(
            title="Other Teacher Course",
            category=self.category,
            instructor=self.other_instructor,
            short_description="Other course",
            full_description="Other course description",
            price=Decimal("19.00"),
            level=Course.Levels.INTERMEDIATE,
            language="English",
            is_published=False,
        )
        other_section = Section.objects.create(course=self.other_course, title="Other section", order_index=1)
        self.other_lesson = Lesson.objects.create(
            section=other_section,
            title="Other lesson",
            order_index=1,
            duration_minutes=8,
            is_preview=False,
            video_url="https://samplelib.com/lib/preview/mp4/sample-5s.mp4",
        )
        self.free_quiz = Quiz.objects.create(
            course=self.free_course,
            title="Free Quiz",
            pass_percent=50,
            is_active=True,
        )
        question = Question.objects.create(
            quiz=self.free_quiz,
            prompt="Pick the correct answer",
            order_index=1,
        )
        self.correct_answer = Answer.objects.create(
            question=question,
            text="Correct",
            is_correct=True,
        )
        Answer.objects.create(
            question=question,
            text="Incorrect",
            is_correct=False,
        )

    def test_free_course_enroll_creates_enrollment_and_payment(self):
        self.client.force_login(self.student)

        response = self.client.post(
            reverse("courses:course_enroll", args=[self.free_course.slug])
        )

        self.assertRedirects(response, self.free_lesson.get_absolute_url())
        self.assertTrue(
            Enrollment.objects.filter(student=self.student, course=self.free_course).exists()
        )
        payment = Payment.objects.get(user=self.student, course=self.free_course)
        self.assertEqual(payment.amount, Decimal("0.00"))
        self.assertEqual(payment.provider, "free")

    def test_paid_course_enroll_redirects_to_checkout(self):
        self.client.force_login(self.student)

        response = self.client.post(
            reverse("courses:course_enroll", args=[self.paid_course.slug])
        )

        self.assertRedirects(
            response,
            reverse("payments:course_checkout", args=[self.paid_course.slug]),
            fetch_redirect_response=False,
        )
        self.assertFalse(
            Enrollment.objects.filter(student=self.student, course=self.paid_course).exists()
        )

    def test_paid_checkout_creates_enrollment_and_payment(self):
        self.client.force_login(self.student)

        response = self.client.post(
            reverse("payments:course_checkout", args=[self.paid_course.slug])
        )

        self.assertRedirects(response, self.preview_lesson.get_absolute_url())
        self.assertTrue(
            Enrollment.objects.filter(student=self.student, course=self.paid_course).exists()
        )
        payment = Payment.objects.get(user=self.student, course=self.paid_course)
        self.assertEqual(payment.amount, Decimal("49.00"))
        self.assertEqual(payment.provider, "demo")

    def test_guest_cannot_open_locked_paid_lesson(self):
        response = self.client.get(self.locked_lesson.get_absolute_url())
        expected_login = f"{reverse('accounts:login')}?next={self.locked_lesson.get_absolute_url()}"
        self.assertRedirects(response, expected_login, fetch_redirect_response=False)

    def test_lesson_auto_syncs_course_from_section(self):
        section = Section.objects.create(course=self.paid_course, title="Auto sync section", order_index=2)
        lesson = Lesson.objects.create(
            section=section,
            title="Synced lesson",
            order_index=5,
            duration_minutes=7,
            video_url="https://samplelib.com/lib/preview/mp4/sample-5s.mp4",
        )

        self.assertEqual(lesson.course, self.paid_course)

    def test_course_only_lesson_creates_default_section(self):
        lesson = Lesson.objects.create(
            course=self.paid_course,
            title="Inline-created lesson",
            order_index=6,
            duration_minutes=9,
            video_url="https://samplelib.com/lib/preview/mp4/sample-10s.mp4",
        )

        self.assertEqual(lesson.course, self.paid_course)
        self.assertIsNotNone(lesson.section)
        self.assertEqual(lesson.section.course, self.paid_course)

    def test_instructor_can_open_teacher_dashboard(self):
        self.client.force_login(self.instructor)
        response = self.client.get(reverse("dashboard:teacher_dashboard"))
        self.assertEqual(response.status_code, 200)

    def test_teacher_course_create_defaults_to_pending(self):
        self.client.force_login(self.instructor)

        response = self.client.post(
            reverse("dashboard:teacher_course_create"),
            {
                "title": "Teacher Flow Course",
                "category": self.category.pk,
                "short_description": "Teacher short description",
                "full_description": "Teacher full description",
                "price": "99.00",
                "discount_price": "79.00",
                "level": Course.Levels.BEGINNER,
                "language": "English",
                "certificate_enabled": "on",
            },
        )

        self.assertRedirects(response, reverse("dashboard:teacher_course_list"))
        course = Course.objects.get(title="Teacher Flow Course")
        self.assertEqual(course.instructor, self.instructor)
        self.assertEqual(course.status, Course.Statuses.PENDING)
        self.assertFalse(course.is_published)

    def test_teacher_cannot_edit_another_teachers_course(self):
        self.client.force_login(self.instructor)

        response = self.client.get(
            reverse("dashboard:teacher_course_edit", args=[self.other_course.pk])
        )

        self.assertEqual(response.status_code, 403)

    def test_teacher_cannot_edit_another_teachers_lesson(self):
        self.client.force_login(self.instructor)

        response = self.client.get(
            reverse("dashboard:teacher_lesson_edit", args=[self.other_lesson.pk])
        )

        self.assertEqual(response.status_code, 403)

    def test_admin_can_approve_pending_teacher_course(self):
        self.client.force_login(self.admin)
        pending_course = Course.objects.create(
            title="Approval Queue Course",
            category=self.category,
            instructor=self.instructor,
            short_description="Approval short",
            full_description="Approval full description",
            price=Decimal("11.00"),
            level=Course.Levels.BEGINNER,
            language="English",
            status=Course.Statuses.PENDING,
            is_published=False,
        )

        response = self.client.post(
            reverse("panel:course_status_update", args=[pending_course.pk, Course.Statuses.ACTIVE])
        )

        self.assertRedirects(response, reverse("panel:course_list"))
        pending_course.refresh_from_db()
        self.assertEqual(pending_course.status, Course.Statuses.ACTIVE)
        self.assertTrue(pending_course.is_published)

    def test_passing_quiz_creates_result(self):
        Enrollment.objects.create(student=self.student, course=self.free_course, price_paid=0)
        self.client.force_login(self.student)
        response = self.client.post(
            reverse("courses:quiz_take", args=[self.free_course.slug, self.free_quiz.id]),
            {f"question_{self.correct_answer.question_id}": self.correct_answer.id},
        )

        result = QuizResult.objects.get(student=self.student, quiz=self.free_quiz)
        self.assertTrue(result.passed)
        self.assertRedirects(
            response,
            reverse("courses:quiz_result", args=[self.free_course.slug, result.id]),
        )

    def test_certificate_page_opens_after_completion_and_pass(self):
        Enrollment.objects.create(student=self.student, course=self.free_course, price_paid=0)
        self.client.force_login(self.student)
        self.client.post(
            reverse("courses:lesson_complete", args=[self.free_course.slug, self.free_lesson.id])
        )
        quiz_result = QuizResult.objects.create(
            student=self.student,
            quiz=self.free_quiz,
            score=1,
            total_questions=1,
            passed=True,
        )
        Certificate.objects.create(
            student=self.student,
            course=self.free_course,
            quiz_result=quiz_result,
        )

        response = self.client.get(
            reverse("courses:certificate_detail", args=[self.free_course.slug])
        )

        self.assertEqual(response.status_code, 200)

    def test_certificate_download_returns_pdf_attachment(self):
        Enrollment.objects.create(student=self.student, course=self.free_course, price_paid=0)
        quiz_result = QuizResult.objects.create(
            student=self.student,
            quiz=self.free_quiz,
            score=1,
            total_questions=1,
            passed=True,
        )
        certificate = Certificate.objects.create(
            student=self.student,
            course=self.free_course,
            quiz_result=quiz_result,
        )
        self.client.force_login(self.student)

        response = self.client.get(
            reverse("courses:certificate_download", args=[self.free_course.slug])
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertIn(certificate.certificate_id, response["Content-Disposition"])

    def test_student_can_delete_own_review(self):
        Enrollment.objects.create(student=self.student, course=self.free_course, price_paid=0)
        Review.objects.create(
            course=self.free_course,
            student=self.student,
            rating=5,
            title="Great course",
            comment="Very helpful",
            is_approved=True,
        )
        self.client.force_login(self.student)

        response = self.client.post(
            reverse("courses:course_review_delete", args=[self.free_course.slug])
        )

        self.assertRedirects(response, self.free_course.get_absolute_url())
        self.assertFalse(
            Review.objects.filter(course=self.free_course, student=self.student).exists()
        )

    def test_quiz_and_curriculum_use_translated_database_content(self):
        self.free_course.title_ru = "Бесплатный курс"
        self.free_course.short_description_ru = "Короткое описание"
        self.free_course.save()
        self.free_lesson.section.title_ru = "Введение"
        self.free_lesson.section.save()
        self.free_quiz.title_ru = "Бесплатный тест"
        self.free_quiz.description_ru = "Описание теста"
        self.free_quiz.save()
        question = self.correct_answer.question
        question.prompt_ru = "Выберите правильный ответ"
        question.save()
        self.correct_answer.text_ru = "Правильно"
        self.correct_answer.save()

        Enrollment.objects.create(student=self.student, course=self.free_course, price_paid=0)
        self.client.force_login(self.student)

        with override("ru"):
            detail_url = self.free_course.get_absolute_url()
            quiz_url = reverse("courses:quiz_take", args=[self.free_course.slug, self.free_quiz.id])

        detail_response = self.client.get(detail_url)
        quiz_response = self.client.get(quiz_url)

        self.assertContains(detail_response, "Введение")
        self.assertContains(detail_response, "Бесплатный тест")
        self.assertContains(quiz_response, "Бесплатный тест")
        self.assertContains(quiz_response, "Выберите правильный ответ")
        self.assertContains(quiz_response, "Правильно")
