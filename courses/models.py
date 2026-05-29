from urllib.parse import parse_qs, urlparse

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Avg, Sum
from django.template.defaultfilters import slugify
from django.urls import reverse
from django.utils.translation import get_language, gettext_lazy as _
from django.utils import timezone


def build_unique_slug(model, value, instance=None):
    base_slug = slugify(value)[:50] or "item"
    slug = base_slug
    index = 1
    queryset = model.objects.all()
    if instance and instance.pk:
        queryset = queryset.exclude(pk=instance.pk)

    while queryset.filter(slug=slug).exists():
        slug = f"{base_slug}-{index}"
        index += 1
    return slug


class Category(models.Model):
    title = models.CharField(max_length=120, unique=True)
    name_uz = models.CharField(max_length=120, blank=True)
    name_ru = models.CharField(max_length=120, blank=True)
    name_en = models.CharField(max_length=120, blank=True)
    slug = models.SlugField(max_length=140, unique=True, blank=True)
    description = models.TextField(blank=True)
    description_uz = models.TextField(blank=True)
    description_ru = models.TextField(blank=True)
    description_en = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["title"]
        verbose_name_plural = "categories"

    def __str__(self):
        return self.title

    def get_translated_title(self, language=None):
        lang = (language or get_language() or "uz").split("-")[0]
        value = getattr(self, f"name_{lang}", "")
        return value or self.title

    def get_translated_description(self, language=None):
        lang = (language or get_language() or "uz").split("-")[0]
        value = getattr(self, f"description_{lang}", "")
        return value or self.description

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = build_unique_slug(Category, self.title, self)
        super().save(*args, **kwargs)


class Course(models.Model):
    class Levels(models.TextChoices):
        BEGINNER = "beginner", _("Beginner")
        INTERMEDIATE = "intermediate", _("Intermediate")
        ADVANCED = "advanced", _("Advanced")

    class Statuses(models.TextChoices):
        PENDING = "pending", _("Pending")
        ACTIVE = "active", _("Active")
        REJECTED = "rejected", _("Rejected")

    title = models.CharField(max_length=180)
    title_uz = models.CharField(max_length=180, blank=True)
    title_ru = models.CharField(max_length=180, blank=True)
    title_en = models.CharField(max_length=180, blank=True)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="courses",
    )
    instructor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="courses_taught",
    )
    thumbnail = models.ImageField(
        upload_to="courses/thumbnails/",
        blank=True,
        null=True,
    )
    short_description = models.CharField(max_length=280)
    short_description_uz = models.CharField(max_length=280, blank=True)
    short_description_ru = models.CharField(max_length=280, blank=True)
    short_description_en = models.CharField(max_length=280, blank=True)
    full_description = models.TextField()
    description_uz = models.TextField(blank=True)
    description_ru = models.TextField(blank=True)
    description_en = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_percent = models.PositiveSmallIntegerField(default=0)
    level = models.CharField(
        max_length=20,
        choices=Levels.choices,
        default=Levels.BEGINNER,
    )
    language = models.CharField(max_length=80, default="English")
    status = models.CharField(
        max_length=20,
        choices=Statuses.choices,
        default=Statuses.PENDING,
    )
    is_published = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    certificate_enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "title"]

    def __str__(self):
        return self.title

    def get_translated_title(self, language=None):
        lang = (language or get_language() or "uz").split("-")[0]
        value = getattr(self, f"title_{lang}", "")
        return value or self.title

    def get_translated_short_description(self, language=None):
        lang = (language or get_language() or "uz").split("-")[0]
        value = getattr(self, f"short_description_{lang}", "")
        return value or self.short_description

    def get_translated_description(self, language=None):
        lang = (language or get_language() or "uz").split("-")[0]
        value = getattr(self, f"description_{lang}", "")
        return value or self.full_description

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = build_unique_slug(Course, self.title, self)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("courses:course_detail", kwargs={"slug": self.slug})

    @property
    def average_rating(self):
        value = self.reviews.filter(is_approved=True).aggregate(avg=Avg("rating"))["avg"]
        return round(value or 0, 1)

    @property
    def review_count(self):
        return self.reviews.filter(is_approved=True).count()

    @property
    def lesson_count(self):
        return self.lessons.count()

    @property
    def section_count(self):
        return self.sections.count()

    @property
    def enrollment_count(self):
        return self.enrollments.count()

    @property
    def total_duration(self):
        return self.lessons.aggregate(total=Sum("duration_minutes"))["total"] or 0

    @property
    def first_lesson(self):
        return (
            self.lessons.select_related("course", "section")
            .order_by("order_index", "section__order_index", "id")
            .first()
        )

    def student_is_enrolled(self, user):
        if not getattr(user, "is_authenticated", False):
            return False
        return self.enrollments.filter(student=user).exists()

    @property
    def final_price(self):
        if not self.discount_percent:
            return self.price
        return self.price - ((self.price * self.discount_percent) / 100)

    @property
    def is_free(self):
        return self.final_price <= 0

    @property
    def preview_lesson_count(self):
        return self.lessons.filter(is_preview=True).count()

    @property
    def has_preview_lessons(self):
        return self.preview_lesson_count > 0

    @property
    def first_preview_lesson(self):
        return (
            self.lessons.filter(is_preview=True)
            .select_related("course", "section")
            .order_by("order_index", "section__order_index", "id")
            .first()
        )

    @property
    def preview_lesson(self):
        return self.first_preview_lesson

    @property
    def preview_player_data(self):
        lesson = self.first_preview_lesson
        return lesson.get_player_data() if lesson else {"type": "missing", "source": ""}

    @property
    def quiz_count(self):
        return self.quizzes.count()

    @property
    def certificate_count(self):
        return self.certificates.count()


class Section(models.Model):
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="sections",
    )
    title = models.CharField(max_length=180)
    description = models.TextField(blank=True)
    order_index = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["order_index", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["course", "order_index"],
                name="unique_section_order_per_course",
            )
        ]

    def __str__(self):
        return f"{self.course.title} - {self.title}"


class Lesson(models.Model):
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="lessons",
        blank=True,
        null=True,
    )
    section = models.ForeignKey(
        Section,
        on_delete=models.CASCADE,
        related_name="lessons",
        blank=True,
        null=True,
    )
    title = models.CharField(max_length=180)
    title_uz = models.CharField(max_length=180, blank=True)
    title_ru = models.CharField(max_length=180, blank=True)
    title_en = models.CharField(max_length=180, blank=True)
    description = models.TextField(blank=True)
    description_uz = models.TextField(blank=True)
    description_ru = models.TextField(blank=True)
    description_en = models.TextField(blank=True)
    video_file = models.FileField(
        upload_to="courses/lessons/",
        blank=True,
        null=True,
    )
    video_url = models.TextField(
        blank=True,
        help_text="Supports direct video URLs or full iframe embed code.",
    )
    duration_minutes = models.PositiveIntegerField(default=0)
    is_preview = models.BooleanField(default=False)
    order_index = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order_index", "section__order_index", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["section", "order_index"],
                name="unique_lesson_order_per_section",
            )
        ]

    def __str__(self):
        course = self.course or (self.section.course if self.section_id else None)
        course_title = course.title if course else "Course"
        return f"{course_title} - {self.title}"

    def get_translated_title(self, language=None):
        lang = (language or get_language() or "uz").split("-")[0]
        value = getattr(self, f"title_{lang}", "")
        return value or self.title

    def get_translated_description(self, language=None):
        lang = (language or get_language() or "uz").split("-")[0]
        value = getattr(self, f"description_{lang}", "")
        return value or self.description

    def get_absolute_url(self):
        course = self.course or (self.section.course if self.section_id else None)
        return reverse(
            "courses:lesson_watch",
            kwargs={"course_slug": course.slug, "lesson_id": self.pk},
        )

    @property
    def duration_seconds(self):
        return self.duration_minutes * 60

    def clean(self):
        super().clean()
        if not self.course and not self.section:
            raise ValidationError(_("Choose a course or section for this lesson."))
        if self.section and self.course and self.section.course_id != self.course_id:
            raise ValidationError(_("The selected section belongs to a different course."))
        if not self.video_file and not (self.video_url or "").strip():
            raise ValidationError(_("Add either an uploaded video file or an external video URL."))

    def save(self, *args, **kwargs):
        if self.section_id and not self.course_id:
            self.course = self.section.course
        elif self.course_id and not self.section_id:
            first_section = self.course.sections.order_by("order_index", "id").first()
            if not first_section:
                first_section = Section.objects.create(
                    course=self.course,
                    title="Main section",
                    description="Auto-created section for direct lesson uploads.",
                    order_index=1,
                )
            self.section = first_section
        elif self.section_id and self.course_id != self.section.course_id:
            self.course = self.section.course
        super().save(*args, **kwargs)

    def _normalized_embed_url(self, value):
        parsed = urlparse(value)
        host = parsed.netloc.lower()

        if "youtube.com" in host:
            video_id = parse_qs(parsed.query).get("v", [""])[0]
            return f"https://www.youtube.com/embed/{video_id}" if video_id else value
        if "youtu.be" in host:
            video_id = parsed.path.strip("/")
            return f"https://www.youtube.com/embed/{video_id}" if video_id else value
        if "vimeo.com" in host:
            video_id = parsed.path.strip("/").split("/")[-1]
            return f"https://player.vimeo.com/video/{video_id}" if video_id else value
        return value

    def get_player_data(self):
        if self.video_file:
            return {"type": "html5", "source": self.video_file.url}

        value = (self.video_url or "").strip()
        if not value:
            return {"type": "missing", "source": ""}
        if "<iframe" in value.lower():
            return {"type": "iframe_html", "source": value}

        lower_value = value.lower()
        if lower_value.endswith((".mp4", ".webm", ".ogg", ".m3u8")):
            return {"type": "html5", "source": value}

        return {"type": "iframe_url", "source": self._normalized_embed_url(value)}


class Enrollment(models.Model):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="enrollments",
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="enrollments",
    )
    price_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-enrolled_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["student", "course"],
                name="unique_student_course_enrollment",
            )
        ]

    def __str__(self):
        return f"{self.student.email} -> {self.course.title}"


class Wishlist(models.Model):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="wishlist_items",
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="wishlists",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["student", "course"],
                name="unique_student_course_wishlist",
            )
        ]

    def __str__(self):
        return f"{self.student.email} saved {self.course.title}"


class Review(models.Model):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reviews",
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="reviews",
    )
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    title = models.CharField(max_length=120, blank=True)
    comment = models.TextField()
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["student", "course"],
                name="unique_student_course_review",
            )
        ]

    def __str__(self):
        return f"{self.course.title} review by {self.student.email}"


class LessonComment(models.Model):
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="lesson_comments",
    )
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Comment on {self.lesson.title} by {self.student.email}"


class WatchProgress(models.Model):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="watch_progress",
    )
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name="progress_entries",
    )
    watched_seconds = models.PositiveIntegerField(default=0)
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(blank=True, null=True)
    last_watched_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-last_watched_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["student", "lesson"],
                name="unique_student_lesson_progress",
            )
        ]

    def __str__(self):
        return f"{self.student.email} - {self.lesson.title}"

    def save(self, *args, **kwargs):
        if self.completed and not self.completed_at:
            self.completed_at = timezone.now()
        if not self.completed:
            self.completed_at = None
        super().save(*args, **kwargs)


class Quiz(models.Model):
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="quizzes",
    )
    title = models.CharField(max_length=180)
    description = models.TextField(blank=True)
    pass_percent = models.PositiveSmallIntegerField(default=70)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["course__title", "title"]

    def __str__(self):
        return f"{self.course.title} - {self.title}"

    @property
    def question_count(self):
        return self.questions.count()


class Question(models.Model):
    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name="questions",
    )
    prompt = models.TextField()
    order_index = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["order_index", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["quiz", "order_index"],
                name="unique_question_order_per_quiz",
            )
        ]

    def __str__(self):
        return f"{self.quiz.title} - Q{self.order_index}"


class Answer(models.Model):
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="answers",
    )
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.text


class QuizResult(models.Model):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="quiz_results",
    )
    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name="results",
    )
    score = models.PositiveIntegerField(default=0)
    total_questions = models.PositiveIntegerField(default=0)
    passed = models.BooleanField(default=False)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-submitted_at"]

    def __str__(self):
        return f"{self.student.email} - {self.quiz.title}"

    @property
    def score_percent(self):
        if not self.total_questions:
            return 0
        return int((self.score / self.total_questions) * 100)


class Certificate(models.Model):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="certificates",
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="certificates",
    )
    quiz_result = models.ForeignKey(
        QuizResult,
        on_delete=models.SET_NULL,
        related_name="certificates",
        blank=True,
        null=True,
    )
    certificate_id = models.CharField(max_length=40, unique=True, blank=True)
    issued_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-issued_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["student", "course"],
                name="unique_student_course_certificate",
            )
        ]

    def __str__(self):
        return f"{self.certificate_id or 'Certificate'} - {self.student.email}"

    def save(self, *args, **kwargs):
        if not self.certificate_id:
            self.certificate_id = f"CERT-{self.course_id or 'X'}-{self.student_id or 'X'}-{timezone.now().strftime('%Y%m%d%H%M%S')}"
        super().save(*args, **kwargs)
