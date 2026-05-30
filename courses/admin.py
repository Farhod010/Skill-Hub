from django.contrib import admin
from django import forms

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
    fields = (
        "title",
        "title_uz",
        "title_ru",
        "title_en",
        "description",
        "description_uz",
        "description_ru",
        "description_en",
        "order_index",
    )


class LessonInlineForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = (
            "title",
            "title_uz",
            "title_ru",
            "title_en",
            "description",
            "description_uz",
            "description_ru",
            "description_en",
            "video_file",
            "video_url",
            "order_index",
            "duration_minutes",
            "is_preview",
        )


class LessonInline(admin.TabularInline):
    model = Lesson
    form = LessonInlineForm
    extra = 1
    fields = (
        "title",
        "title_uz",
        "title_ru",
        "title_en",
        "description",
        "description_uz",
        "description_ru",
        "description_en",
        "video_file",
        "video_url",
        "order_index",
        "duration_minutes",
        "is_preview",
    )
    ordering = ("order_index", "id")
    show_change_link = True


class QuizInline(admin.TabularInline):
    model = Quiz
    extra = 0
    fields = (
        "title",
        "title_uz",
        "title_ru",
        "title_en",
        "description",
        "description_uz",
        "description_ru",
        "description_en",
        "pass_percent",
        "is_active",
    )


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "instructor",
        "category",
        "price",
        "status",
        "created_at",
    )
    list_filter = ("category", "level", "status", "is_published", "is_featured")
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
    ordering = ("-created_at", "title")
    readonly_fields = ("created_at", "updated_at")
    inlines = [LessonInline, SectionInline, QuizInline]
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "title",
                    "title_uz",
                    "title_ru",
                    "title_en",
                    "slug",
                    "category",
                    "instructor",
                    "thumbnail",
                    "preview_video",
                )
            },
        ),
        (
            "Descriptions",
            {
                "fields": (
                    "short_description",
                    "short_description_uz",
                    "short_description_ru",
                    "short_description_en",
                    "full_description",
                    "description_uz",
                    "description_ru",
                    "description_en",
                )
            },
        ),
        (
            "Commerce and publishing",
            {
                "fields": (
                    "price",
                    "discount_price",
                    "discount_percent",
                    "level",
                    "language",
                    "status",
                    "moderation_notes",
                    "is_published",
                    "is_featured",
                    "certificate_enabled",
                )
            },
        ),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        if request.user.is_superuser:
            return queryset
        if getattr(request.user, "role", None) == getattr(request.user, "Roles", None).INSTRUCTOR:
            return queryset.filter(instructor=request.user)
        return queryset

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "instructor" and not request.user.is_superuser:
            if getattr(request.user, "role", None) == getattr(request.user, "Roles", None).INSTRUCTOR:
                kwargs["queryset"] = db_field.remote_field.model.objects.filter(pk=request.user.pk)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "order_index")
    list_filter = ("course",)
    search_fields = ("title", "title_uz", "title_ru", "title_en", "course__title", "course__title_uz", "course__title_ru", "course__title_en")


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "course",
        "order_index",
        "has_video_source",
        "is_preview",
        "created_at",
    )
    list_filter = ("is_preview", "course", "course__category")
    search_fields = ("title", "title_uz", "title_ru", "title_en", "course__title", "course__instructor__email")
    ordering = ("course", "order_index", "id")
    readonly_fields = ("created_at", "updated_at")

    @admin.display(boolean=True, description="Video")
    def has_video_source(self, obj):
        return bool(obj.video_file or obj.video_url)

    def get_queryset(self, request):
        queryset = super().get_queryset(request).select_related("course", "section")
        if request.user.is_superuser:
            return queryset
        if getattr(request.user, "role", None) == getattr(request.user, "Roles", None).INSTRUCTOR:
            return queryset.filter(course__instructor=request.user)
        return queryset


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
    search_fields = (
        "title",
        "title_uz",
        "title_ru",
        "title_en",
        "description",
        "description_uz",
        "description_ru",
        "description_en",
        "course__title",
        "course__title_uz",
        "course__title_ru",
        "course__title_en",
    )


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("quiz", "order_index")
    list_filter = ("quiz",)
    search_fields = (
        "prompt",
        "prompt_uz",
        "prompt_ru",
        "prompt_en",
        "quiz__title",
        "quiz__title_uz",
        "quiz__title_ru",
        "quiz__title_en",
    )


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ("question", "text", "is_correct")
    list_filter = ("is_correct",)
    search_fields = (
        "text",
        "text_uz",
        "text_ru",
        "text_en",
        "question__prompt",
        "question__prompt_uz",
        "question__prompt_ru",
        "question__prompt_en",
    )


@admin.register(QuizResult)
class QuizResultAdmin(admin.ModelAdmin):
    list_display = ("student", "quiz", "score", "total_questions", "passed", "submitted_at")
    list_filter = ("passed", "quiz__course")
    search_fields = ("student__email", "quiz__title")


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ("certificate_id", "student", "course", "issued_at")
    search_fields = ("certificate_id", "student__email", "course__title")
