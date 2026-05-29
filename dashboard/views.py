from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Avg, Count, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from accounts.forms import UserPanelCreationForm, UserPanelForm
from accounts.models import User
from courses.forms import AnswerForm, CategoryForm, CourseForm, LessonForm, QuestionForm, QuizForm, SectionForm
from courses.models import (
    Answer,
    Certificate,
    Category,
    Course,
    Enrollment,
    Lesson,
    Question,
    Quiz,
    QuizResult,
    Review,
    Section,
    WatchProgress,
    Wishlist,
)
from payments.models import Payment
from site_settings.forms import SiteSettingForm
from site_settings.models import SiteSetting

from .permissions import panel_access_required


def paginate_queryset(request, queryset, per_page=12):
    paginator = Paginator(queryset, per_page)
    return paginator.get_page(request.GET.get("page"))


def enforce_superuser_guard(request, target_user):
    if target_user.is_superuser and not request.user.is_superuser:
        raise PermissionDenied(_("Only a superuser can manage another superuser."))


@login_required
def student_dashboard(request):
    if request.user.can_access_panel:
        return redirect(request.user.home_url)

    enrollments = (
        Enrollment.objects.filter(student=request.user)
        .select_related("course__category", "course__instructor")
        .prefetch_related("course__sections__lessons")
    )
    completed_lesson_ids = set(
        WatchProgress.objects.filter(student=request.user, completed=True).values_list(
            "lesson_id", flat=True
        )
    )
    dashboard_courses = []
    for enrollment in enrollments:
        course = enrollment.course
        lessons = []
        for section in course.sections.all():
            lessons.extend(list(section.lessons.all()))
        total_lessons = len(lessons)
        completed_lessons = sum(1 for lesson in lessons if lesson.id in completed_lesson_ids)
        next_lesson = next(
            (lesson for lesson in lessons if lesson.id not in completed_lesson_ids),
            lessons[0] if lessons else None,
        )
        progress_percent = int((completed_lessons / total_lessons) * 100) if total_lessons else 0
        dashboard_courses.append(
            {
                "course": course,
                "enrollment": enrollment,
                "total_lessons": total_lessons,
                "completed_lessons": completed_lessons,
                "progress_percent": progress_percent,
                "next_lesson": next_lesson,
            }
        )

    wishlist_items = (
        Wishlist.objects.filter(student=request.user)
        .select_related("course__category", "course__instructor")
        .order_by("-created_at")
    )
    featured_course = next(
        (item for item in dashboard_courses if item["next_lesson"]),
        dashboard_courses[0] if dashboard_courses else None,
    )
    recent_activity = (
        WatchProgress.objects.filter(student=request.user)
        .select_related("lesson__section", "lesson__section__course")
        .order_by("-last_watched_at")[:5]
    )
    quiz_results_queryset = QuizResult.objects.filter(student=request.user).select_related(
        "quiz", "quiz__course"
    )
    quiz_results = (
        quiz_results_queryset
        .order_by("-submitted_at")[:6]
    )
    certificates_queryset = Certificate.objects.filter(student=request.user).select_related(
        "course", "course__instructor"
    )
    certificates = (
        certificates_queryset
        .order_by("-issued_at")[:6]
    )
    payments = (
        Payment.objects.filter(user=request.user)
        .select_related("course")
        .order_by("-created_at")[:6]
    )
    recommended_courses = (
        Course.objects.filter(is_published=True)
        .exclude(enrollments__student=request.user)
        .select_related("category", "instructor")[:3]
    )
    completed_courses = sum(1 for item in dashboard_courses if item["progress_percent"] == 100)
    context = {
        "enrolled_courses": dashboard_courses,
        "featured_course": featured_course,
        "wishlist_items": wishlist_items,
        "recent_activity": recent_activity,
        "quiz_results": quiz_results,
        "certificates": certificates,
        "payments": payments,
        "recommended_courses": recommended_courses,
        "stats": {
            "enrolled_courses": len(dashboard_courses),
            "wishlist_courses": wishlist_items.count(),
            "completed_lessons": len(completed_lesson_ids),
            "completed_courses": completed_courses,
            "certificates": certificates_queryset.count(),
            "quiz_passes": quiz_results_queryset.filter(passed=True).count(),
        },
    }
    return render(request, "dashboard/student_dashboard.html", context)


@login_required
def teacher_dashboard(request):
    if request.user.can_access_panel:
        return redirect(request.user.home_url)
    if request.user.role != User.Roles.INSTRUCTOR:
        return redirect("dashboard:student_dashboard")

    courses = (
        Course.objects.filter(instructor=request.user)
        .select_related("category")
        .prefetch_related("sections__lessons", "quizzes")
        .order_by("-created_at")
    )
    course_ids = list(courses.values_list("id", flat=True))
    enrollments = Enrollment.objects.filter(course_id__in=course_ids)
    reviews = Review.objects.filter(course_id__in=course_ids, is_approved=True)
    total_revenue = (
        Payment.objects.filter(
            course_id__in=course_ids,
            status=Payment.Status.COMPLETED,
        ).aggregate(total=Sum("amount"))["total"]
        or 0
    )
    top_course = (
        courses.annotate(total_students=Count("enrollments"))
        .order_by("-total_students", "title")
        .first()
    )
    context = {
        "teacher_courses": courses,
        "recent_enrollments": enrollments.select_related("student", "course").order_by("-enrolled_at")[:6],
        "recent_payments": Payment.objects.filter(course_id__in=course_ids).select_related("user", "course").order_by("-created_at")[:6],
        "recent_results": QuizResult.objects.filter(quiz__course_id__in=course_ids).select_related("student", "quiz", "quiz__course").order_by("-submitted_at")[:6],
        "recent_reviews": reviews.select_related("student", "course").order_by("-created_at")[:6],
        "stats": {
            "courses": courses.count(),
            "students": enrollments.values("student").distinct().count(),
            "revenue": total_revenue,
            "average_rating": round(reviews.aggregate(avg=Avg("rating"))["avg"] or 0, 1)
            if reviews.exists()
            else 0,
            "top_course": top_course,
            "quizzes": Quiz.objects.filter(course_id__in=course_ids).count(),
        },
    }
    return render(request, "dashboard/teacher_dashboard.html", context)


def teacher_required(view_func):
    @login_required
    def wrapped(request, *args, **kwargs):
        if request.user.role != User.Roles.INSTRUCTOR:
            return redirect(request.user.home_url)
        return view_func(request, *args, **kwargs)

    return wrapped


@teacher_required
def teacher_course_create(request):
    form = CourseForm(request.POST or None, request.FILES or None, actor=request.user)
    if request.method == "POST" and form.is_valid():
        course = form.save(commit=False)
        course.instructor = request.user
        course.status = Course.Statuses.PENDING
        course.is_published = False
        course.save()
        messages.success(request, _("Course created and sent for review."))
        return redirect("dashboard:teacher_dashboard")
    return render(
        request,
        "dashboard/teacher_form.html",
        {"form": form, "page_title": _("Create course"), "submit_label": _("Save course")},
    )


@teacher_required
def teacher_course_edit(request, pk):
    course = get_object_or_404(Course, pk=pk, instructor=request.user)
    form = CourseForm(request.POST or None, request.FILES or None, instance=course, actor=request.user)
    if request.method == "POST" and form.is_valid():
        course = form.save(commit=False)
        course.instructor = request.user
        course.save()
        messages.success(request, _("Course updated successfully."))
        return redirect("dashboard:teacher_dashboard")
    return render(
        request,
        "dashboard/teacher_form.html",
        {
            "form": form,
            "page_title": _("Edit %(title)s") % {"title": course.get_translated_title()},
            "submit_label": _("Update course"),
        },
    )


@teacher_required
def teacher_lesson_create(request):
    form = LessonForm(request.POST or None, request.FILES or None, actor=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, _("Lesson added successfully."))
        return redirect("dashboard:teacher_dashboard")
    return render(
        request,
        "dashboard/teacher_form.html",
        {"form": form, "page_title": _("Add lesson"), "submit_label": _("Save lesson")},
    )


@teacher_required
def teacher_quiz_create(request):
    form = QuizForm(request.POST or None, actor=request.user)
    if request.method == "POST" and form.is_valid():
        quiz = form.save()
        messages.success(request, _("Quiz created successfully."))
        return redirect("dashboard:teacher_question_create", quiz_id=quiz.id)
    return render(
        request,
        "dashboard/teacher_form.html",
        {"form": form, "page_title": _("Create quiz"), "submit_label": _("Save quiz")},
    )


@teacher_required
def teacher_question_create(request, quiz_id):
    quiz = get_object_or_404(Quiz, pk=quiz_id, course__instructor=request.user)
    question_form = QuestionForm(request.POST or None, prefix="question", actor=request.user)
    answer_form = AnswerForm(request.POST or None, prefix="answer", actor=request.user)
    question_form.fields.pop("quiz", None)
    answer_form.fields.pop("question", None)
    if request.method == "POST" and question_form.is_valid() and answer_form.is_valid():
        question = question_form.save(commit=False)
        question.quiz = quiz
        question.save()
        answer = answer_form.save(commit=False)
        answer.question = question
        answer.save()
        messages.success(
            request,
            _("Question and answer saved. Add more from the admin panel if needed."),
        )
        return redirect("dashboard:teacher_dashboard")
    return render(
        request,
        "dashboard/teacher_question_form.html",
        {
            "quiz": quiz,
            "question_form": question_form,
            "answer_form": answer_form,
        },
    )


@panel_access_required
def panel_dashboard(request):
    stats = {
        "total_users": User.objects.count(),
        "total_courses": Course.objects.count(),
        "total_lessons": Lesson.objects.count(),
        "total_payments": Payment.objects.count(),
        "pending_courses": Course.objects.filter(status=Course.Statuses.PENDING).count(),
        "total_earnings": Payment.objects.filter(status=Payment.Status.COMPLETED).aggregate(
            total=Sum("amount")
        )["total"]
        or 0,
        "total_enrollments": Enrollment.objects.count(),
        "completed_watch_stats": WatchProgress.objects.filter(completed=True).count(),
    }
    context = {
        "stats": stats,
        "recent_users": User.objects.order_by("-date_joined")[:6],
        "popular_courses": Course.objects.annotate(
            total_enrollments=Count("enrollments", distinct=True),
            total_lessons=Count("lessons", distinct=True),
        ).order_by("-total_enrollments", "title")[:6],
        "recent_payments": Payment.objects.select_related("user", "course").order_by("-created_at")[:6],
        "recent_reviews": Review.objects.select_related("course", "student").order_by("-created_at")[
            :6
        ],
    }
    return render(request, "dashboard/panel/index.html", context)


@panel_access_required
def panel_user_create(request):
    form = UserPanelCreationForm(request.POST or None, request.FILES or None, actor=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, _("User created successfully."))
        return redirect("panel:user_list")
    return render(
        request,
        "dashboard/panel/users/form.html",
        {"form": form, "page_title": _("Create user")},
    )


@panel_access_required
def panel_user_list(request):
    query = request.GET.get("q", "").strip()
    role = request.GET.get("role", "").strip()
    status = request.GET.get("status", "").strip()
    sort = request.GET.get("sort", "newest").strip()
    users = User.objects.all()
    if query:
        users = users.filter(
            Q(email__icontains=query)
            | Q(username__icontains=query)
            | Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
            | Q(role__icontains=query)
        )
    if role:
        users = users.filter(role=role)
    if status == "active":
        users = users.filter(is_active=True, is_blocked=False)
    elif status == "blocked":
        users = users.filter(is_blocked=True)

    if sort == "oldest":
        users = users.order_by("date_joined")
    elif sort == "name":
        users = users.order_by("first_name", "last_name", "username")
    else:
        users = users.order_by("-date_joined")

    all_users = User.objects.all()
    context = {
        "page_obj": paginate_queryset(request, users),
        "search_query": query,
        "selected_role": role,
        "selected_status": status,
        "selected_sort": sort,
        "role_choices": User.Roles.choices,
        "create_form": UserPanelCreationForm(actor=request.user),
        "stats": {
            "total": all_users.count(),
            "active": all_users.filter(is_active=True, is_blocked=False).count(),
            "blocked": all_users.filter(is_blocked=True).count(),
            "instructors": all_users.filter(role=User.Roles.INSTRUCTOR).count(),
            "students": all_users.filter(role=User.Roles.STUDENT).count(),
            "moderators": all_users.filter(role=User.Roles.MODERATOR).count(),
        },
    }
    return render(request, "dashboard/panel/users/list.html", context)


@panel_access_required
def panel_user_edit(request, pk):
    user_obj = get_object_or_404(User, pk=pk)
    enforce_superuser_guard(request, user_obj)
    form = UserPanelForm(
        request.POST or None,
        request.FILES or None,
        instance=user_obj,
        actor=request.user,
    )
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, _("User updated successfully."))
        return redirect("panel:user_list")
    return render(
        request,
        "dashboard/panel/users/form.html",
        {"form": form, "page_title": _("Edit %(name)s") % {"name": user_obj.full_name}},
    )


@panel_access_required
def panel_user_delete(request, pk):
    user_obj = get_object_or_404(User, pk=pk)
    enforce_superuser_guard(request, user_obj)
    if request.method == "POST":
        user_obj.delete()
        messages.success(request, _("User deleted successfully."))
        return redirect("panel:user_list")
    return render(
        request,
        "dashboard/panel/confirm_delete.html",
        {
            "page_title": _("Delete user"),
            "object_label": user_obj.email,
            "cancel_url": "panel:user_list",
        },
    )


@panel_access_required
@require_POST
def panel_user_toggle_block(request, pk):
    user_obj = get_object_or_404(User, pk=pk)
    enforce_superuser_guard(request, user_obj)
    user_obj.is_blocked = not user_obj.is_blocked
    user_obj.save(update_fields=["is_blocked"])
    state = _("blocked") if user_obj.is_blocked else _("unblocked")
    messages.success(request, _("User has been %(state)s.") % {"state": state})
    return redirect("panel:user_list")


@panel_access_required
def panel_course_list(request):
    query = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()
    category = request.GET.get("category", "").strip()
    sort = request.GET.get("sort", "newest").strip()
    courses = Course.objects.select_related("category", "instructor").annotate(
        total_lessons=Count("lessons", distinct=True),
        total_students=Count("enrollments", distinct=True),
    )
    if query:
        courses = courses.filter(
            Q(title__icontains=query)
            | Q(title_uz__icontains=query)
            | Q(title_ru__icontains=query)
            | Q(title_en__icontains=query)
            | Q(category__title__icontains=query)
            | Q(category__name_uz__icontains=query)
            | Q(category__name_ru__icontains=query)
            | Q(category__name_en__icontains=query)
            | Q(instructor__email__icontains=query)
        )
    if category:
        courses = courses.filter(category_id=category)
    if status == "published":
        courses = courses.filter(is_published=True)
    elif status == "draft":
        courses = courses.filter(is_published=False)
    elif status in {choice for choice, _label in Course.Statuses.choices}:
        courses = courses.filter(status=status)
    elif status == "featured":
        courses = courses.filter(is_featured=True)

    if sort == "oldest":
        courses = courses.order_by("created_at")
    elif sort == "title":
        courses = courses.order_by("title")
    elif sort == "students":
        courses = courses.order_by("-total_students", "title")
    else:
        courses = courses.order_by("-created_at")

    all_courses = Course.objects.all()
    context = {
        "page_obj": paginate_queryset(request, courses),
        "search_query": query,
        "selected_status": status,
        "selected_category": category,
        "selected_sort": sort,
        "categories": Category.objects.order_by("title"),
        "stats": {
            "total": all_courses.count(),
            "published": all_courses.filter(is_published=True).count(),
            "pending": all_courses.filter(status=Course.Statuses.PENDING).count(),
            "featured": all_courses.filter(is_featured=True).count(),
            "rejected": all_courses.filter(status=Course.Statuses.REJECTED).count(),
            "active": all_courses.filter(status=Course.Statuses.ACTIVE).count(),
        },
    }
    return render(request, "dashboard/panel/courses/list.html", context)


@panel_access_required
def panel_course_create(request):
    form = CourseForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, _("Course created successfully."))
        return redirect("panel:course_list")
    return render(
        request,
        "dashboard/panel/courses/form.html",
        {"form": form, "page_title": _("Create course")},
    )


@panel_access_required
def panel_course_edit(request, pk):
    course = get_object_or_404(Course, pk=pk)
    form = CourseForm(request.POST or None, request.FILES or None, instance=course)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, _("Course updated successfully."))
        return redirect("panel:course_list")
    return render(
        request,
        "dashboard/panel/courses/form.html",
        {"form": form, "page_title": _("Edit %(title)s") % {"title": course.get_translated_title()}},
    )


@panel_access_required
def panel_course_delete(request, pk):
    course = get_object_or_404(Course, pk=pk)
    if request.method == "POST":
        course.delete()
        messages.success(request, _("Course deleted successfully."))
        return redirect("panel:course_list")
    return render(
        request,
        "dashboard/panel/confirm_delete.html",
        {
            "page_title": _("Delete course"),
            "object_label": course.get_translated_title(),
            "cancel_url": "panel:course_list",
        },
    )


@panel_access_required
@require_POST
def panel_course_publish_toggle(request, pk):
    course = get_object_or_404(Course, pk=pk)
    course.is_published = not course.is_published
    course.save(update_fields=["is_published"])
    messages.success(request, _("Course publish status updated."))
    return redirect("panel:course_list")


@panel_access_required
@require_POST
def panel_course_featured_toggle(request, pk):
    course = get_object_or_404(Course, pk=pk)
    course.is_featured = not course.is_featured
    course.save(update_fields=["is_featured"])
    messages.success(request, _("Course featured status updated."))
    return redirect("panel:course_list")


@panel_access_required
def panel_category_list(request):
    query = request.GET.get("q", "").strip()
    categories = Category.objects.all().order_by("title")
    if query:
        categories = categories.filter(
            Q(title__icontains=query)
            | Q(name_uz__icontains=query)
            | Q(name_ru__icontains=query)
            | Q(name_en__icontains=query)
            | Q(description__icontains=query)
            | Q(description_uz__icontains=query)
            | Q(description_ru__icontains=query)
            | Q(description_en__icontains=query)
        )
    context = {"page_obj": paginate_queryset(request, categories), "search_query": query}
    return render(request, "dashboard/panel/categories/list.html", context)


@panel_access_required
def panel_category_create(request):
    form = CategoryForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, _("Category created successfully."))
        return redirect("panel:category_list")
    return render(
        request,
        "dashboard/panel/categories/form.html",
        {"form": form, "page_title": _("Create category")},
    )


@panel_access_required
def panel_category_edit(request, pk):
    category = get_object_or_404(Category, pk=pk)
    form = CategoryForm(request.POST or None, instance=category)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, _("Category updated successfully."))
        return redirect("panel:category_list")
    return render(
        request,
        "dashboard/panel/categories/form.html",
        {
            "form": form,
            "page_title": _("Edit %(title)s") % {"title": category.get_translated_title()},
        },
    )


@panel_access_required
def panel_category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == "POST":
        category.delete()
        messages.success(request, _("Category deleted successfully."))
        return redirect("panel:category_list")
    return render(
        request,
        "dashboard/panel/confirm_delete.html",
        {
            "page_title": _("Delete category"),
            "object_label": category.get_translated_title(),
            "cancel_url": "panel:category_list",
        },
    )


@panel_access_required
@require_POST
def panel_category_toggle(request, pk):
    category = get_object_or_404(Category, pk=pk)
    category.is_active = not category.is_active
    category.save(update_fields=["is_active"])
    messages.success(request, _("Category availability updated."))
    return redirect("panel:category_list")


@panel_access_required
def panel_section_list(request):
    query = request.GET.get("q", "").strip()
    sections = Section.objects.select_related("course").order_by("course__title", "order_index")
    if query:
        sections = sections.filter(Q(title__icontains=query) | Q(course__title__icontains=query))
    context = {"page_obj": paginate_queryset(request, sections), "search_query": query}
    return render(request, "dashboard/panel/sections/list.html", context)


@panel_access_required
def panel_section_create(request):
    form = SectionForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, _("Section created successfully."))
        return redirect("panel:section_list")
    return render(
        request,
        "dashboard/panel/sections/form.html",
        {"form": form, "page_title": _("Create section")},
    )


@panel_access_required
def panel_section_edit(request, pk):
    section = get_object_or_404(Section, pk=pk)
    form = SectionForm(request.POST or None, instance=section)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, _("Section updated successfully."))
        return redirect("panel:section_list")
    return render(
        request,
        "dashboard/panel/sections/form.html",
        {"form": form, "page_title": _("Edit %(title)s") % {"title": section.title}},
    )


@panel_access_required
def panel_section_delete(request, pk):
    section = get_object_or_404(Section, pk=pk)
    if request.method == "POST":
        section.delete()
        messages.success(request, _("Section deleted successfully."))
        return redirect("panel:section_list")
    return render(
        request,
        "dashboard/panel/confirm_delete.html",
        {
            "page_title": _("Delete section"),
            "object_label": section.title,
            "cancel_url": "panel:section_list",
        },
    )


@panel_access_required
def panel_lesson_list(request):
    query = request.GET.get("q", "").strip()
    course = request.GET.get("course", "").strip()
    sort = request.GET.get("sort", "course").strip()
    lessons = Lesson.objects.select_related("course", "section", "section__course")
    if query:
        lessons = lessons.filter(
            Q(title__icontains=query)
            | Q(title_uz__icontains=query)
            | Q(title_ru__icontains=query)
            | Q(title_en__icontains=query)
            | Q(section__title__icontains=query)
            | Q(course__title__icontains=query)
            | Q(course__title_uz__icontains=query)
            | Q(course__title_ru__icontains=query)
            | Q(course__title_en__icontains=query)
            | Q(section__course__title__icontains=query)
            | Q(section__course__title_uz__icontains=query)
            | Q(section__course__title_ru__icontains=query)
            | Q(section__course__title_en__icontains=query)
        )
    if course:
        lessons = lessons.filter(course_id=course)

    if sort == "latest":
        lessons = lessons.order_by("-created_at")
    else:
        lessons = lessons.order_by("course__title", "section__order_index", "order_index", "id")

    all_lessons = Lesson.objects.all()
    context = {
        "page_obj": paginate_queryset(request, lessons),
        "search_query": query,
        "selected_course": course,
        "selected_sort": sort,
        "courses": Course.objects.order_by("title"),
        "stats": {
            "total": all_lessons.count(),
            "preview": all_lessons.filter(is_preview=True).count(),
            "video_uploads": all_lessons.exclude(video_file="").count(),
            "external_videos": all_lessons.exclude(video_url="").count(),
        },
    }
    return render(request, "dashboard/panel/lessons/list.html", context)


@panel_access_required
def panel_lesson_create(request):
    initial = {}
    if request.method != "POST":
        course_id = request.GET.get("course")
        if course_id:
            course = get_object_or_404(Course, pk=course_id)
            initial["course"] = course
            first_section = course.sections.order_by("order_index", "id").first()
            if first_section:
                initial["section"] = first_section

    form = LessonForm(request.POST or None, request.FILES or None, initial=initial or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, _("Lesson created successfully."))
        return redirect("panel:lesson_list")
    return render(
        request,
        "dashboard/panel/lessons/form.html",
        {"form": form, "page_title": _("Create lesson")},
    )


@panel_access_required
def panel_lesson_edit(request, pk):
    lesson = get_object_or_404(Lesson, pk=pk)
    form = LessonForm(request.POST or None, request.FILES or None, instance=lesson)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, _("Lesson updated successfully."))
        return redirect("panel:lesson_list")
    return render(
        request,
        "dashboard/panel/lessons/form.html",
        {"form": form, "page_title": _("Edit %(title)s") % {"title": lesson.get_translated_title()}},
    )


@panel_access_required
def panel_lesson_delete(request, pk):
    lesson = get_object_or_404(Lesson, pk=pk)
    if request.method == "POST":
        lesson.delete()
        messages.success(request, _("Lesson deleted successfully."))
        return redirect("panel:lesson_list")
    return render(
        request,
        "dashboard/panel/confirm_delete.html",
        {
            "page_title": _("Delete lesson"),
            "object_label": lesson.get_translated_title(),
            "cancel_url": "panel:lesson_list",
        },
    )


@panel_access_required
def panel_quiz_list(request):
    query = request.GET.get("q", "").strip()
    quizzes = Quiz.objects.select_related("course").order_by("course__title", "title")
    if query:
        quizzes = quizzes.filter(Q(title__icontains=query) | Q(course__title__icontains=query))
    return render(
        request,
        "dashboard/panel/quizzes/list.html",
        {"page_obj": paginate_queryset(request, quizzes), "search_query": query},
    )


@panel_access_required
def panel_quiz_create(request):
    form = QuizForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, _("Quiz created successfully."))
        return redirect("panel:quiz_list")
    return render(
        request,
        "dashboard/panel/quizzes/form.html",
        {"form": form, "page_title": _("Create quiz")},
    )


@panel_access_required
def panel_quiz_edit(request, pk):
    quiz = get_object_or_404(Quiz, pk=pk)
    form = QuizForm(request.POST or None, instance=quiz)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, _("Quiz updated successfully."))
        return redirect("panel:quiz_list")
    return render(
        request,
        "dashboard/panel/quizzes/form.html",
        {"form": form, "page_title": _("Edit %(title)s") % {"title": quiz.title}},
    )


@panel_access_required
def panel_quiz_delete(request, pk):
    quiz = get_object_or_404(Quiz, pk=pk)
    if request.method == "POST":
        quiz.delete()
        messages.success(request, _("Quiz deleted successfully."))
        return redirect("panel:quiz_list")
    return render(
        request,
        "dashboard/panel/confirm_delete.html",
        {
            "page_title": _("Delete quiz"),
            "object_label": quiz.title,
            "cancel_url": "panel:quiz_list",
        },
    )


@panel_access_required
def panel_question_list(request):
    query = request.GET.get("q", "").strip()
    questions = Question.objects.select_related("quiz", "quiz__course").order_by(
        "quiz__course__title",
        "quiz__title",
        "order_index",
    )
    if query:
        questions = questions.filter(
            Q(prompt__icontains=query)
            | Q(quiz__title__icontains=query)
            | Q(quiz__course__title__icontains=query)
        )
    return render(
        request,
        "dashboard/panel/questions/list.html",
        {"page_obj": paginate_queryset(request, questions), "search_query": query},
    )


@panel_access_required
def panel_question_create(request):
    form = QuestionForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, _("Question created successfully."))
        return redirect("panel:question_list")
    return render(
        request,
        "dashboard/panel/questions/form.html",
        {"form": form, "page_title": _("Create question")},
    )


@panel_access_required
def panel_question_edit(request, pk):
    question = get_object_or_404(Question, pk=pk)
    form = QuestionForm(request.POST or None, instance=question)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, _("Question updated successfully."))
        return redirect("panel:question_list")
    return render(
        request,
        "dashboard/panel/questions/form.html",
        {"form": form, "page_title": _("Edit question %(number)s") % {"number": question.order_index}},
    )


@panel_access_required
def panel_question_delete(request, pk):
    question = get_object_or_404(Question, pk=pk)
    if request.method == "POST":
        question.delete()
        messages.success(request, _("Question deleted successfully."))
        return redirect("panel:question_list")
    return render(
        request,
        "dashboard/panel/confirm_delete.html",
        {
            "page_title": _("Delete question"),
            "object_label": question.prompt[:80],
            "cancel_url": "panel:question_list",
        },
    )


@panel_access_required
def panel_answer_list(request):
    query = request.GET.get("q", "").strip()
    answers = Answer.objects.select_related("question", "question__quiz", "question__quiz__course").order_by(
        "question__quiz__course__title",
        "question__quiz__title",
        "question__order_index",
        "id",
    )
    if query:
        answers = answers.filter(
            Q(text__icontains=query)
            | Q(question__prompt__icontains=query)
            | Q(question__quiz__title__icontains=query)
        )
    return render(
        request,
        "dashboard/panel/answers/list.html",
        {"page_obj": paginate_queryset(request, answers), "search_query": query},
    )


@panel_access_required
def panel_answer_create(request):
    form = AnswerForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, _("Answer created successfully."))
        return redirect("panel:answer_list")
    return render(
        request,
        "dashboard/panel/answers/form.html",
        {"form": form, "page_title": _("Create answer")},
    )


@panel_access_required
def panel_answer_edit(request, pk):
    answer = get_object_or_404(Answer, pk=pk)
    form = AnswerForm(request.POST or None, instance=answer)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, _("Answer updated successfully."))
        return redirect("panel:answer_list")
    return render(
        request,
        "dashboard/panel/answers/form.html",
        {"form": form, "page_title": _("Edit answer #%(number)s") % {"number": answer.pk}},
    )


@panel_access_required
def panel_answer_delete(request, pk):
    answer = get_object_or_404(Answer, pk=pk)
    if request.method == "POST":
        answer.delete()
        messages.success(request, _("Answer deleted successfully."))
        return redirect("panel:answer_list")
    return render(
        request,
        "dashboard/panel/confirm_delete.html",
        {
            "page_title": _("Delete answer"),
            "object_label": answer.text,
            "cancel_url": "panel:answer_list",
        },
    )


@panel_access_required
def panel_quiz_result_list(request):
    query = request.GET.get("q", "").strip()
    results = QuizResult.objects.select_related("student", "quiz", "quiz__course").order_by("-submitted_at")
    if query:
        results = results.filter(
            Q(student__email__icontains=query)
            | Q(quiz__title__icontains=query)
            | Q(quiz__course__title__icontains=query)
        )
    return render(
        request,
        "dashboard/panel/quiz_results/list.html",
        {"page_obj": paginate_queryset(request, results), "search_query": query},
    )


@panel_access_required
def panel_certificate_list(request):
    query = request.GET.get("q", "").strip()
    certificates = Certificate.objects.select_related("student", "course", "course__instructor").order_by("-issued_at")
    if query:
        certificates = certificates.filter(
            Q(certificate_id__icontains=query)
            | Q(student__email__icontains=query)
            | Q(course__title__icontains=query)
            | Q(course__title_uz__icontains=query)
            | Q(course__title_ru__icontains=query)
            | Q(course__title_en__icontains=query)
        )
    return render(
        request,
        "dashboard/panel/certificates/list.html",
        {"page_obj": paginate_queryset(request, certificates), "search_query": query},
    )


@panel_access_required
def panel_certificate_delete(request, pk):
    certificate = get_object_or_404(Certificate, pk=pk)
    if request.method == "POST":
        certificate.delete()
        messages.success(request, _("Certificate deleted successfully."))
        return redirect("panel:certificate_list")
    return render(
        request,
        "dashboard/panel/confirm_delete.html",
        {
            "page_title": _("Delete certificate"),
            "object_label": certificate.certificate_id,
            "cancel_url": "panel:certificate_list",
        },
    )


@panel_access_required
def panel_review_list(request):
    query = request.GET.get("q", "").strip()
    approval = request.GET.get("approval", "").strip()
    reviews = Review.objects.select_related("course", "student").order_by("-created_at")
    if query:
        reviews = reviews.filter(
            Q(course__title__icontains=query)
            | Q(course__title_uz__icontains=query)
            | Q(course__title_ru__icontains=query)
            | Q(course__title_en__icontains=query)
            | Q(student__email__icontains=query)
            | Q(title__icontains=query)
            | Q(comment__icontains=query)
        )
    if approval == "approved":
        reviews = reviews.filter(is_approved=True)
    elif approval == "pending":
        reviews = reviews.filter(is_approved=False)
    context = {
        "page_obj": paginate_queryset(request, reviews),
        "search_query": query,
        "approval": approval,
    }
    return render(request, "dashboard/panel/reviews/list.html", context)


@panel_access_required
@require_POST
def panel_review_toggle(request, pk):
    review = get_object_or_404(Review, pk=pk)
    review.is_approved = not review.is_approved
    review.save(update_fields=["is_approved"])
    messages.success(request, _("Review moderation status updated."))
    return redirect("panel:review_list")


@panel_access_required
def panel_review_delete(request, pk):
    review = get_object_or_404(Review, pk=pk)
    if request.method == "POST":
        review.delete()
        messages.success(request, _("Review deleted successfully."))
        return redirect("panel:review_list")
    return render(
        request,
        "dashboard/panel/confirm_delete.html",
        {
            "page_title": _("Delete review"),
            "object_label": _("%(course)s review by %(student)s")
            % {"course": review.course.get_translated_title(), "student": review.student.email},
            "cancel_url": "panel:review_list",
        },
    )


@panel_access_required
def panel_payment_list(request):
    query = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()
    payments = Payment.objects.select_related("user", "course").order_by("-created_at")
    if query:
        payments = payments.filter(
            Q(reference__icontains=query)
            | Q(user__email__icontains=query)
            | Q(course__title__icontains=query)
            | Q(course__title_uz__icontains=query)
            | Q(course__title_ru__icontains=query)
            | Q(course__title_en__icontains=query)
        )
    if status:
        payments = payments.filter(status=status)
    return render(
        request,
        "dashboard/panel/payments/list.html",
        {
            "page_obj": paginate_queryset(request, payments),
            "search_query": query,
            "selected_status": status,
            "payment_statuses": Payment.Status.choices,
        },
    )


@panel_access_required
def panel_site_settings(request):
    site_setting = SiteSetting.get_solo()
    form = SiteSettingForm(request.POST or None, request.FILES or None, instance=site_setting)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, _("Site settings updated successfully."))
        return redirect("panel:site_settings")
    return render(
        request,
        "dashboard/panel/settings/form.html",
        {"form": form, "page_title": _("Site settings")},
    )
