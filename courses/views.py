import json
from io import BytesIO

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, Prefetch, Q, Sum
from django.http import Http404, JsonResponse
from django.http import FileResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import gettext as _
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.views.generic import DetailView, ListView, TemplateView
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from .forms import LessonCommentForm, ReviewForm
from .models import (
    Certificate,
    Answer,
    Category,
    Course,
    Enrollment,
    Lesson,
    LessonComment,
    Question,
    Quiz,
    QuizResult,
    Review,
    Section,
    WatchProgress,
    Wishlist,
)
from .services import (
    enroll_user_in_course,
    issue_certificate_if_eligible,
    student_completed_course,
    student_passed_course_quiz,
    user_has_course_access,
)


def get_course_queryset_for_user(user):
    queryset = Course.objects.select_related("category", "instructor").prefetch_related(
        Prefetch(
            "sections",
            queryset=Section.objects.prefetch_related("lessons"),
        )
    )
    if getattr(user, "is_authenticated", False) and user.can_access_panel:
        return queryset
    if getattr(user, "is_authenticated", False) and user.role == user.Roles.INSTRUCTOR:
        return queryset.filter(Q(is_published=True) | Q(instructor=user)).distinct()
    return queryset.filter(is_published=True)


def user_can_watch_lesson(user, lesson):
    course = lesson.section.course
    if lesson.is_preview:
        return True
    return user_has_course_access(user, course)


class LandingPageView(TemplateView):
    template_name = "landing.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["featured_courses"] = (
            Course.objects.filter(is_published=True, is_featured=True)
            .select_related("category", "instructor")
            .prefetch_related("reviews")
            [:6]
        )
        context["categories"] = Category.objects.filter(is_active=True)[:8]
        context["testimonials"] = (
            Review.objects.filter(is_approved=True)
            .select_related("student", "course")
            .order_by("-created_at")[:3]
        )
        context["stats"] = {
            "courses": Course.objects.filter(is_published=True).count(),
            "students": Enrollment.objects.values("student").distinct().count(),
            "instructors": Course.objects.values("instructor").distinct().count(),
        }
        return context


class CourseListView(ListView):
    template_name = "courses/course_list.html"
    context_object_name = "courses"
    paginate_by = 9

    def get_queryset(self):
        queryset = (
            Course.objects.filter(is_published=True)
            .select_related("category", "instructor")
            .annotate(
                popularity_score=Count("enrollments", distinct=True),
                rating_score=Avg("reviews__rating", filter=Q(reviews__is_approved=True)),
            )
        )
        query = self.request.GET.get("q", "").strip()
        category = self.request.GET.get("category", "").strip()
        level = self.request.GET.get("level", "").strip()
        price_type = self.request.GET.get("price", "").strip()
        ordering = self.request.GET.get("sort", "newest").strip()

        if query:
            queryset = queryset.filter(
                Q(title__icontains=query)
                | Q(title_uz__icontains=query)
                | Q(title_ru__icontains=query)
                | Q(title_en__icontains=query)
                | Q(short_description__icontains=query)
                | Q(short_description_uz__icontains=query)
                | Q(short_description_ru__icontains=query)
                | Q(short_description_en__icontains=query)
                | Q(full_description__icontains=query)
                | Q(description_uz__icontains=query)
                | Q(description_ru__icontains=query)
                | Q(description_en__icontains=query)
                | Q(instructor__first_name__icontains=query)
                | Q(instructor__last_name__icontains=query)
            )
        if category:
            queryset = queryset.filter(category__slug=category)
        if level:
            queryset = queryset.filter(level=level)
        if price_type == "free":
            queryset = queryset.filter(price=0)
        elif price_type == "paid":
            queryset = queryset.filter(price__gt=0)

        ordering_map = {
            "newest": "-created_at",
            "price_low": "price",
            "price_high": "-price",
            "title": "title",
            "popular": "-popularity_score",
            "rating": "-rating_score",
        }
        return queryset.order_by(ordering_map.get(ordering, "-created_at"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = Category.objects.filter(is_active=True)
        context["selected_category"] = self.request.GET.get("category", "")
        context["selected_level"] = self.request.GET.get("level", "")
        context["selected_price"] = self.request.GET.get("price", "")
        context["selected_sort"] = self.request.GET.get("sort", "newest")
        context["search_query"] = self.request.GET.get("q", "")
        context["levels"] = Course.Levels.choices
        context["result_count"] = context["page_obj"].paginator.count
        return context


class CourseDetailView(DetailView):
    template_name = "courses/course_detail.html"
    context_object_name = "course"
    slug_field = "slug"

    def get_queryset(self):
        return get_course_queryset_for_user(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course = self.object
        user = self.request.user
        user_review = None
        if user.is_authenticated:
            user_review = Review.objects.filter(course=course, student=user).first()

        context["sections"] = course.sections.all()
        context["is_enrolled"] = course.student_is_enrolled(user)
        context["can_access_full_course"] = user_has_course_access(user, course)
        context["is_wishlisted"] = user.is_authenticated and Wishlist.objects.filter(
            course=course,
            student=user,
        ).exists()
        context["reviews"] = course.reviews.filter(is_approved=True).select_related("student")
        context["user_review"] = user_review
        context["can_review"] = user.is_authenticated and (
            context["is_enrolled"] or user.can_access_panel
        )
        context["review_form"] = ReviewForm(instance=user_review)
        context["first_preview_lesson"] = course.first_preview_lesson
        context["preview_lesson_count"] = course.preview_lesson_count
        context["quizzes"] = course.quizzes.filter(is_active=True).prefetch_related("questions")
        context["passed_quiz_result"] = (
            student_passed_course_quiz(user, course) if user.is_authenticated else None
        )
        context["certificate"] = (
            Certificate.objects.filter(student=user, course=course).first()
            if user.is_authenticated
            else None
        )
        context["course_completed"] = (
            student_completed_course(user, course)
            if user.is_authenticated and context["can_access_full_course"]
            else False
        )
        context["related_courses"] = (
            Course.objects.filter(
                is_published=True,
                category=course.category,
            )
            .exclude(pk=course.pk)
            .select_related("category", "instructor")[:3]
        )
        return context


class LessonWatchView(DetailView):
    template_name = "courses/lesson_watch.html"
    context_object_name = "lesson"
    pk_url_kwarg = "lesson_id"
    model = Lesson

    def get_object(self, queryset=None):
        queryset = (
            Lesson.objects.select_related(
                "section",
                "section__course",
                "section__course__instructor",
            )
            .prefetch_related("comments__student")
        )
        lesson = get_object_or_404(
            queryset,
            pk=self.kwargs["lesson_id"],
            section__course__slug=self.kwargs["course_slug"],
        )
        course = lesson.section.course
        if not course.is_published and not (
            self.request.user.is_authenticated
            and (self.request.user.can_access_panel or course.instructor_id == self.request.user.id)
        ):
            raise Http404("Course not found.")
        if not user_can_watch_lesson(self.request.user, lesson):
            messages.error(
                self.request,
                _("Enroll in this course to access the full lesson library."),
            )
            return redirect(course.get_absolute_url())
        return lesson

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        if hasattr(obj, "status_code"):
            return obj
        self.object = obj
        context = self.get_context_data(object=obj)
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        lesson = self.object
        course = lesson.section.course
        progress = None
        completed_lesson_ids = set()
        if self.request.user.is_authenticated:
            progress = WatchProgress.objects.filter(
                student=self.request.user,
                lesson=lesson,
            ).first()
            completed_lesson_ids = set(
                WatchProgress.objects.filter(
                    student=self.request.user,
                    lesson__section__course=course,
                    completed=True,
                ).values_list("lesson_id", flat=True)
            )

        ordered_lessons = list(
            Lesson.objects.filter(section__course=course)
            .select_related("section", "section__course")
            .order_by("section__order_index", "order_index", "id")
        )
        lesson_index = next(
            (index for index, item in enumerate(ordered_lessons) if item.id == lesson.id),
            0,
        )
        previous_lesson = ordered_lessons[lesson_index - 1] if lesson_index > 0 else None
        next_lesson = (
            ordered_lessons[lesson_index + 1]
            if lesson_index < len(ordered_lessons) - 1
            else None
        )
        completed_lessons_count = sum(
            1 for ordered_lesson in ordered_lessons if ordered_lesson.id in completed_lesson_ids
        )

        context["course"] = course
        context["sections"] = course.sections.prefetch_related("lessons")
        context["player"] = lesson.get_player_data()
        context["progress"] = progress
        context["comment_form"] = LessonCommentForm()
        context["comments"] = lesson.comments.select_related("student")[:10]
        context["is_enrolled"] = course.student_is_enrolled(self.request.user)
        context["can_access_full_course"] = (
            self.request.user.is_authenticated
            and (
                context["is_enrolled"]
                or self.request.user.can_access_panel
                or course.instructor_id == self.request.user.id
            )
        )
        context["completed_lesson_ids"] = completed_lesson_ids
        context["previous_lesson"] = previous_lesson
        context["next_lesson"] = next_lesson
        context["lesson_position"] = lesson_index + 1
        context["course_total_lessons"] = len(ordered_lessons)
        context["course_completed_lessons"] = completed_lessons_count
        context["course_progress_percent"] = (
            int((completed_lessons_count / len(ordered_lessons)) * 100)
            if ordered_lessons
            else 0
        )
        return context


@login_required
@require_POST
def enroll_in_course(request, slug):
    course = get_object_or_404(Course, slug=slug, is_published=True)
    if user_has_course_access(request.user, course):
        messages.info(request, _("You already have access to this course."))
        return redirect(course.get_absolute_url())

    if course.is_free:
        enrollment, payment, created = enroll_user_in_course(
            request.user,
            course,
            amount=0,
            provider="free",
        )
        if created:
            messages.success(
                request,
                _("You are now enrolled in %(course)s.")
                % {"course": course.get_translated_title()},
            )
        else:
            messages.info(request, _("You are already enrolled in this course."))
        if course.first_lesson:
            return redirect(course.first_lesson.get_absolute_url())
        return redirect(course.get_absolute_url())

    messages.info(request, _("Complete the demo checkout to unlock the full course."))
    return redirect("payments:course_checkout", slug=course.slug)


@login_required
@require_POST
def toggle_wishlist(request, slug):
    course = get_object_or_404(Course, slug=slug, is_published=True)
    wishlist_item, created = Wishlist.objects.get_or_create(student=request.user, course=course)
    if created:
        messages.success(request, _("Course added to your wishlist."))
    else:
        wishlist_item.delete()
        messages.info(request, _("Course removed from your wishlist."))
    return redirect(course.get_absolute_url())


@login_required
@require_POST
def submit_review(request, slug):
    course = get_object_or_404(Course, slug=slug, is_published=True)
    if not course.student_is_enrolled(request.user) and not request.user.can_access_panel:
        messages.error(request, _("You need to enroll before leaving a review."))
        return redirect(course.get_absolute_url())

    instance = Review.objects.filter(course=course, student=request.user).first()
    form = ReviewForm(request.POST, instance=instance)
    if form.is_valid():
        review = form.save(commit=False)
        review.course = course
        review.student = request.user
        if not request.user.can_access_panel:
            review.is_approved = False
        review.save()
        messages.success(
            request,
            _("Your review has been saved and is waiting for moderation."),
        )
    else:
        messages.error(request, _("Please correct the review form and try again."))
    return redirect(course.get_absolute_url())


@login_required
@require_POST
def delete_review(request, slug):
    course = get_object_or_404(Course, slug=slug, is_published=True)
    review = get_object_or_404(Review, course=course, student=request.user)
    review.delete()
    messages.success(request, _("Your review has been deleted."))
    return redirect(course.get_absolute_url())


@login_required
@require_POST
def add_lesson_comment(request, course_slug, lesson_id):
    lesson = get_object_or_404(
        Lesson.objects.select_related("section", "section__course"),
        pk=lesson_id,
        section__course__slug=course_slug,
    )
    if not user_can_watch_lesson(request.user, lesson):
        messages.error(request, _("You cannot comment on lessons you cannot access."))
        return redirect(lesson.section.course.get_absolute_url())

    form = LessonCommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.lesson = lesson
        comment.student = request.user
        comment.save()
        messages.success(request, _("Your comment was added."))
    else:
        messages.error(request, _("Please write a comment before submitting."))
    return redirect(lesson.get_absolute_url())


@login_required
@require_POST
def mark_lesson_completed(request, course_slug, lesson_id):
    lesson = get_object_or_404(
        Lesson.objects.select_related("section", "section__course"),
        pk=lesson_id,
        section__course__slug=course_slug,
    )
    if not user_can_watch_lesson(request.user, lesson):
        messages.error(request, _("You do not have access to this lesson."))
        return redirect(lesson.section.course.get_absolute_url())

    progress, progress_created = WatchProgress.objects.get_or_create(
        student=request.user,
        lesson=lesson,
    )
    progress.completed = True
    progress.watched_seconds = max(progress.watched_seconds, lesson.duration_seconds)
    progress.save()
    issue_certificate_if_eligible(request.user, lesson.section.course)
    messages.success(request, _("Lesson marked as completed."))
    return redirect(lesson.get_absolute_url())


@login_required
@require_POST
def save_watch_progress(request, course_slug, lesson_id):
    lesson = get_object_or_404(
        Lesson.objects.select_related("section", "section__course"),
        pk=lesson_id,
        section__course__slug=course_slug,
    )
    if not user_can_watch_lesson(request.user, lesson):
        return JsonResponse({"detail": "Forbidden"}, status=403)

    payload = {}
    if request.body:
        try:
            payload = json.loads(request.body.decode("utf-8"))
        except json.JSONDecodeError:
            payload = {}
    watched_seconds = int(payload.get("watched_seconds") or request.POST.get("watched_seconds") or 0)
    completed = bool(payload.get("completed"))

    progress, progress_created = WatchProgress.objects.get_or_create(
        student=request.user,
        lesson=lesson,
    )
    progress.watched_seconds = max(progress.watched_seconds, watched_seconds)

    if lesson.duration_seconds:
        completion_threshold = int(lesson.duration_seconds * 0.9)
        if progress.watched_seconds >= completion_threshold:
            completed = True

    progress.completed = progress.completed or completed
    progress.save()
    if progress.completed:
        issue_certificate_if_eligible(request.user, lesson.section.course)
    return JsonResponse(
        {
            "completed": progress.completed,
            "watched_seconds": progress.watched_seconds,
        }
    )


@login_required
def take_quiz(request, slug, quiz_id):
    course = get_object_or_404(Course, slug=slug, is_published=True)
    quiz = get_object_or_404(
        Quiz.objects.filter(course=course, is_active=True).prefetch_related("questions__answers"),
        pk=quiz_id,
    )
    if not user_has_course_access(request.user, course):
        messages.error(request, _("You need course access before taking this quiz."))
        return redirect(course.get_absolute_url())

    if request.method == "POST":
        questions = list(quiz.questions.all())
        score = 0
        for question in questions:
            selected_answer_id = request.POST.get(f"question_{question.id}")
            if not selected_answer_id:
                continue
            is_correct = question.answers.filter(pk=selected_answer_id, is_correct=True).exists()
            if is_correct:
                score += 1
        total_questions = len(questions)
        score_percent = int((score / total_questions) * 100) if total_questions else 0
        result = QuizResult.objects.create(
            student=request.user,
            quiz=quiz,
            score=score,
            total_questions=total_questions,
            passed=score_percent >= quiz.pass_percent,
        )
        if result.passed:
            issue_certificate_if_eligible(request.user, course)
            messages.success(
                request,
                _("You passed the quiz with %(percent)s%%.") % {"percent": score_percent},
            )
        else:
            messages.info(
                request,
                _("You scored %(percent)s%%. You can try again.") % {"percent": score_percent},
            )
        return redirect("courses:quiz_result", slug=course.slug, result_id=result.id)

    return render(
        request,
        "courses/quiz_take.html",
        {"course": course, "quiz": quiz},
    )


@login_required
def quiz_result_detail(request, slug, result_id):
    result = get_object_or_404(
        QuizResult.objects.select_related("quiz", "quiz__course", "student"),
        pk=result_id,
        student=request.user,
        quiz__course__slug=slug,
    )
    return render(
        request,
        "courses/quiz_result.html",
        {
            "course": result.quiz.course,
            "result": result,
        },
    )


@login_required
def certificate_detail(request, slug):
    certificate = get_object_or_404(
        Certificate.objects.select_related("course", "course__instructor", "student"),
        student=request.user,
        course__slug=slug,
    )
    return render(
        request,
        "courses/certificate_detail.html",
        {"certificate": certificate, "course": certificate.course},
    )


@login_required
def certificate_download(request, slug):
    certificate = get_object_or_404(
        Certificate.objects.select_related("course", "course__instructor", "student"),
        student=request.user,
        course__slug=slug,
    )
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    pdf.setTitle(f"{certificate.course.title} Certificate")
    pdf.setFont("Helvetica-Bold", 24)
    pdf.drawCentredString(width / 2, height - 100, "Certificate of Completion")
    pdf.setFont("Helvetica", 14)
    pdf.drawCentredString(width / 2, height - 150, "This certifies that")
    pdf.setFont("Helvetica-Bold", 28)
    pdf.drawCentredString(width / 2, height - 200, certificate.student.full_name)
    pdf.setFont("Helvetica", 14)
    pdf.drawCentredString(width / 2, height - 245, "has successfully completed")
    pdf.setFont("Helvetica-Bold", 20)
    pdf.drawCentredString(width / 2, height - 290, certificate.course.title)
    pdf.setFont("Helvetica", 12)
    pdf.drawCentredString(
        width / 2,
        height - 340,
        f"Instructor: {certificate.course.instructor.full_name}",
    )
    pdf.drawCentredString(
        width / 2,
        height - 365,
        f"Issued: {certificate.issued_at.strftime('%B %d, %Y')}",
    )
    pdf.drawCentredString(
        width / 2,
        height - 390,
        f"Certificate ID: {certificate.certificate_id}",
    )
    pdf.showPage()
    pdf.save()
    buffer.seek(0)
    return FileResponse(
        buffer,
        as_attachment=True,
        filename=f"{certificate.certificate_id}.pdf",
        content_type="application/pdf",
    )
