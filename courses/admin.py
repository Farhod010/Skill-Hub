from django.contrib import admin

from .models import (
    Answer,
    Certificate,
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


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("title", "name_uz", "name_ru", "name_en", "is_active", "updated_at")
    prepopulated_fields = {"slug": ("title",)}
    search_fields = ("title", "name_uz", "name_ru", "name_en")


class SectionInline(admin.TabularInline):
    model = Section
    extra = 0


class QuizInline(admin.TabularInline):
    model = Quiz
    extra = 0


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "title_uz",
        "title_ru",
        "title_en",
        "category",
        "instructor",
        "price",
        "is_published",
        "is_featured",
    )
    list_filter = ("category", "level", "is_published", "is_featured")
    search_fields = (
        "title",
        "title_uz",
        "title_ru",
        "title_en",
        "short_description",
        "short_description_uz",
        "short_description_ru",
        "short_description_en",
        "instructor__email",
    )
    prepopulated_fields = {"slug": ("title",)}
    inlines = [SectionInline, QuizInline]


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "order_index")
    list_filter = ("course",)
    search_fields = ("title", "course__title")


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "title_uz",
        "title_ru",
        "title_en",
        "section",
        "duration_minutes",
        "is_preview",
        "order_index",
    )
    list_filter = ("is_preview", "section__course")
    search_fields = ("title", "title_uz", "title_ru", "title_en", "section__title", "section__course__title")


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ("student", "course", "price_paid", "enrolled_at")
    search_fields = ("student__email", "course__title")


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ("student", "course", "created_at")
    search_fields = ("student__email", "course__title")


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("course", "student", "rating", "is_approved", "created_at")
    list_filter = ("is_approved", "rating")
    search_fields = ("course__title", "student__email", "title", "comment")


@admin.register(LessonComment)
class LessonCommentAdmin(admin.ModelAdmin):
    list_display = ("lesson", "student", "created_at")
    search_fields = ("lesson__title", "student__email", "comment")


@admin.register(WatchProgress)
class WatchProgressAdmin(admin.ModelAdmin):
    list_display = ("student", "lesson", "watched_seconds", "completed", "last_watched_at")
    list_filter = ("completed",)
    search_fields = ("student__email", "lesson__title")


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "pass_percent", "is_active")
    list_filter = ("is_active", "course")
    search_fields = ("title", "course__title")


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("quiz", "order_index")
    list_filter = ("quiz",)
    search_fields = ("prompt", "quiz__title")


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ("question", "text", "is_correct")
    list_filter = ("is_correct",)
    search_fields = ("text", "question__prompt")


@admin.register(QuizResult)
class QuizResultAdmin(admin.ModelAdmin):
    list_display = ("student", "quiz", "score", "total_questions", "passed", "submitted_at")
    list_filter = ("passed", "quiz__course")
    search_fields = ("student__email", "quiz__title")


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ("certificate_id", "student", "course", "issued_at")
    search_fields = ("certificate_id", "student__email", "course__title")
