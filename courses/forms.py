from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from accounts.models import User

from .models import Answer, Category, Course, Lesson, LessonComment, Question, Quiz, Review, Section


class StyledModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs.setdefault("class", "checkbox-input")
            elif isinstance(widget, forms.FileInput):
                widget.attrs.setdefault("class", "file-input")
            else:
                widget.attrs.setdefault("class", "input")


class CategoryForm(StyledModelForm):
    class Meta:
        model = Category
        fields = (
            "title",
            "name_uz",
            "name_ru",
            "name_en",
            "slug",
            "description",
            "description_uz",
            "description_ru",
            "description_en",
            "is_active",
        )
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
            "description_uz": forms.Textarea(attrs={"rows": 3}),
            "description_ru": forms.Textarea(attrs={"rows": 3}),
            "description_en": forms.Textarea(attrs={"rows": 3}),
        }
        labels = {
            "title": _("Default title"),
            "name_uz": _("Title (Uzbek)"),
            "name_ru": _("Title (Russian)"),
            "name_en": _("Title (English)"),
            "slug": _("Slug"),
            "description": _("Default description"),
            "description_uz": _("Description (Uzbek)"),
            "description_ru": _("Description (Russian)"),
            "description_en": _("Description (English)"),
            "is_active": _("Active"),
        }


class CourseForm(StyledModelForm):
    def __init__(self, *args, actor=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.actor = actor
        self.fields["instructor"].queryset = User.objects.filter(
            role__in=[User.Roles.INSTRUCTOR, User.Roles.ADMIN]
        ).order_by("first_name", "last_name", "email")
        if actor and getattr(actor, "role", None) == User.Roles.INSTRUCTOR and not actor.can_access_panel:
            self.fields["instructor"].queryset = User.objects.filter(pk=actor.pk)
            self.fields["instructor"].initial = actor
            self.fields["instructor"].disabled = True

    class Meta:
        model = Course
        fields = (
            "title",
            "title_uz",
            "title_ru",
            "title_en",
            "slug",
            "category",
            "instructor",
            "thumbnail",
            "preview_video",
            "short_description",
            "short_description_uz",
            "short_description_ru",
            "short_description_en",
            "full_description",
            "description_uz",
            "description_ru",
            "description_en",
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
        widgets = {
            "short_description": forms.Textarea(attrs={"rows": 3}),
            "short_description_uz": forms.Textarea(attrs={"rows": 2}),
            "short_description_ru": forms.Textarea(attrs={"rows": 2}),
            "short_description_en": forms.Textarea(attrs={"rows": 2}),
            "full_description": forms.Textarea(attrs={"rows": 8}),
            "description_uz": forms.Textarea(attrs={"rows": 4}),
            "description_ru": forms.Textarea(attrs={"rows": 4}),
            "description_en": forms.Textarea(attrs={"rows": 4}),
        }
        labels = {
            "title": _("Default title"),
            "title_uz": _("Title (Uzbek)"),
            "title_ru": _("Title (Russian)"),
            "title_en": _("Title (English)"),
            "slug": _("Slug"),
            "category": _("Category"),
            "instructor": _("Instructor"),
            "thumbnail": _("Thumbnail"),
            "preview_video": _("Preview video"),
            "short_description": _("Default short description"),
            "short_description_uz": _("Short description (Uzbek)"),
            "short_description_ru": _("Short description (Russian)"),
            "short_description_en": _("Short description (English)"),
            "full_description": _("Default full description"),
            "description_uz": _("Full description (Uzbek)"),
            "description_ru": _("Full description (Russian)"),
            "description_en": _("Full description (English)"),
            "price": _("Price"),
            "discount_price": _("Discount price"),
            "discount_percent": _("Discount percent"),
            "level": _("Level"),
            "language": _("Language"),
            "status": _("Status"),
            "moderation_notes": _("Moderation notes"),
            "is_published": _("Published"),
            "is_featured": _("Featured"),
            "certificate_enabled": _("Certificate enabled"),
        }

    def clean_instructor(self):
        instructor = self.cleaned_data.get("instructor") or getattr(self, "actor", None)
        if instructor.role not in {User.Roles.INSTRUCTOR, User.Roles.ADMIN}:
            raise ValidationError(_("Only instructors or admins can be assigned to a course."))
        return instructor


class TeacherCourseForm(StyledModelForm):
    class Meta:
        model = Course
        fields = (
            "title",
            "title_uz",
            "title_ru",
            "title_en",
            "category",
            "thumbnail",
            "preview_video",
            "short_description",
            "short_description_uz",
            "short_description_ru",
            "short_description_en",
            "full_description",
            "description_uz",
            "description_ru",
            "description_en",
            "price",
            "discount_price",
            "level",
            "language",
            "certificate_enabled",
        )
        widgets = {
            "short_description": forms.Textarea(attrs={"rows": 3}),
            "short_description_uz": forms.Textarea(attrs={"rows": 2}),
            "short_description_ru": forms.Textarea(attrs={"rows": 2}),
            "short_description_en": forms.Textarea(attrs={"rows": 2}),
            "full_description": forms.Textarea(attrs={"rows": 8}),
            "description_uz": forms.Textarea(attrs={"rows": 4}),
            "description_ru": forms.Textarea(attrs={"rows": 4}),
            "description_en": forms.Textarea(attrs={"rows": 4}),
        }
        labels = {
            "title": _("Default title"),
            "title_uz": _("Title (Uzbek)"),
            "title_ru": _("Title (Russian)"),
            "title_en": _("Title (English)"),
            "category": _("Category"),
            "thumbnail": _("Thumbnail"),
            "preview_video": _("Preview video"),
            "short_description": _("Default short description"),
            "short_description_uz": _("Short description (Uzbek)"),
            "short_description_ru": _("Short description (Russian)"),
            "short_description_en": _("Short description (English)"),
            "full_description": _("Default full description"),
            "description_uz": _("Full description (Uzbek)"),
            "description_ru": _("Full description (Russian)"),
            "description_en": _("Full description (English)"),
            "price": _("Price"),
            "discount_price": _("Discount price"),
            "level": _("Level"),
            "language": _("Language"),
            "certificate_enabled": _("Certificate enabled"),
        }

class SectionForm(StyledModelForm):
    def __init__(self, *args, actor=None, **kwargs):
        super().__init__(*args, **kwargs)
        if actor and getattr(actor, "role", None) == User.Roles.INSTRUCTOR and not actor.can_access_panel:
            self.fields["course"].queryset = Course.objects.filter(instructor=actor).order_by("title")

    class Meta:
        model = Section
        fields = (
            "course",
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
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
            "description_uz": forms.Textarea(attrs={"rows": 3}),
            "description_ru": forms.Textarea(attrs={"rows": 3}),
            "description_en": forms.Textarea(attrs={"rows": 3}),
        }
        labels = {
            "course": _("Course"),
            "title": _("Default title"),
            "title_uz": _("Title (Uzbek)"),
            "title_ru": _("Title (Russian)"),
            "title_en": _("Title (English)"),
            "description": _("Default description"),
            "description_uz": _("Description (Uzbek)"),
            "description_ru": _("Description (Russian)"),
            "description_en": _("Description (English)"),
            "order_index": _("Order"),
        }


class LessonForm(StyledModelForm):
    def __init__(self, *args, actor=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["section"].required = False
        if actor and getattr(actor, "role", None) == User.Roles.INSTRUCTOR and not actor.can_access_panel:
            self.fields["course"].queryset = Course.objects.filter(instructor=actor).order_by("title")
            self.fields["section"].queryset = Section.objects.filter(course__instructor=actor).order_by(
                "course__title",
                "order_index",
            )

    class Meta:
        model = Lesson
        fields = (
            "course",
            "section",
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
            "duration_minutes",
            "is_preview",
            "order_index",
        )
        widgets = {
            "description": forms.Textarea(attrs={"rows": 5}),
            "description_uz": forms.Textarea(attrs={"rows": 3}),
            "description_ru": forms.Textarea(attrs={"rows": 3}),
            "description_en": forms.Textarea(attrs={"rows": 3}),
            "video_url": forms.Textarea(
                attrs={"rows": 3, "placeholder": _("Paste a video URL or iframe embed code")}
            ),
        }
        labels = {
            "course": _("Course"),
            "section": _("Section"),
            "title": _("Default title"),
            "title_uz": _("Title (Uzbek)"),
            "title_ru": _("Title (Russian)"),
            "title_en": _("Title (English)"),
            "description": _("Default description"),
            "description_uz": _("Description (Uzbek)"),
            "description_ru": _("Description (Russian)"),
            "description_en": _("Description (English)"),
            "video_file": _("Uploaded video"),
            "video_url": _("External video URL or embed"),
            "duration_minutes": _("Duration in minutes"),
            "is_preview": _("Preview lesson"),
            "order_index": _("Order"),
        }

    def clean(self):
        cleaned_data = super().clean()
        course = cleaned_data.get("course")
        section = cleaned_data.get("section")
        video_file = cleaned_data.get("video_file")
        video_url = (cleaned_data.get("video_url") or "").strip()
        if section and not course:
            cleaned_data["course"] = section.course
            course = section.course
        if course and section and section.course_id != course.id:
            raise ValidationError(_("The selected section belongs to another course."))
        if not course and not section:
            raise ValidationError(_("Choose which course this lesson belongs to."))
        if not video_file and not video_url:
            raise ValidationError(_("Add either an uploaded video file or an external video URL."))
        return cleaned_data


class TeacherLessonForm(LessonForm):
    def __init__(self, *args, actor=None, course=None, **kwargs):
        super().__init__(*args, actor=actor, **kwargs)
        if course is not None:
            self.fields["course"].initial = course
            self.fields["section"].queryset = Section.objects.filter(course=course).order_by(
                "order_index",
                "id",
            )

        self.fields["course"].help_text = _("Choose which of your courses this lesson belongs to.")
        self.fields["order_index"].help_text = _("Use lesson order to control the playback sequence.")


class ReviewForm(StyledModelForm):
    class Meta:
        model = Review
        fields = ("rating", "title", "comment")
        widgets = {
            "comment": forms.Textarea(attrs={"rows": 4}),
        }


class LessonCommentForm(StyledModelForm):
    class Meta:
        model = LessonComment
        fields = ("comment",)
        widgets = {
            "comment": forms.Textarea(attrs={"rows": 3, "placeholder": _("Ask a question or leave a note...")})
        }


class QuizForm(StyledModelForm):
    def __init__(self, *args, actor=None, **kwargs):
        super().__init__(*args, **kwargs)
        if actor and getattr(actor, "role", None) == User.Roles.INSTRUCTOR and not actor.can_access_panel:
            self.fields["course"].queryset = Course.objects.filter(instructor=actor).order_by("title")

    class Meta:
        model = Quiz
        fields = (
            "course",
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
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
            "description_uz": forms.Textarea(attrs={"rows": 3}),
            "description_ru": forms.Textarea(attrs={"rows": 3}),
            "description_en": forms.Textarea(attrs={"rows": 3}),
        }
        labels = {
            "course": _("Course"),
            "title": _("Default title"),
            "title_uz": _("Title (Uzbek)"),
            "title_ru": _("Title (Russian)"),
            "title_en": _("Title (English)"),
            "description": _("Default description"),
            "description_uz": _("Description (Uzbek)"),
            "description_ru": _("Description (Russian)"),
            "description_en": _("Description (English)"),
            "pass_percent": _("Pass percent"),
            "is_active": _("Active"),
        }


class QuestionForm(StyledModelForm):
    def __init__(self, *args, actor=None, **kwargs):
        super().__init__(*args, **kwargs)
        if actor and getattr(actor, "role", None) == User.Roles.INSTRUCTOR and not actor.can_access_panel:
            self.fields["quiz"].queryset = Quiz.objects.filter(course__instructor=actor).order_by(
                "course__title",
                "title",
            )

    class Meta:
        model = Question
        fields = ("quiz", "prompt", "prompt_uz", "prompt_ru", "prompt_en", "order_index")
        widgets = {
            "prompt": forms.Textarea(attrs={"rows": 4}),
            "prompt_uz": forms.Textarea(attrs={"rows": 3}),
            "prompt_ru": forms.Textarea(attrs={"rows": 3}),
            "prompt_en": forms.Textarea(attrs={"rows": 3}),
        }
        labels = {
            "quiz": _("Quiz"),
            "prompt": _("Default prompt"),
            "prompt_uz": _("Prompt (Uzbek)"),
            "prompt_ru": _("Prompt (Russian)"),
            "prompt_en": _("Prompt (English)"),
            "order_index": _("Order"),
        }


class AnswerForm(StyledModelForm):
    def __init__(self, *args, actor=None, **kwargs):
        super().__init__(*args, **kwargs)
        if actor and getattr(actor, "role", None) == User.Roles.INSTRUCTOR and not actor.can_access_panel:
            self.fields["question"].queryset = Question.objects.filter(
                quiz__course__instructor=actor
            ).order_by("quiz__course__title", "quiz__title", "order_index")

    class Meta:
        model = Answer
        fields = ("question", "text", "text_uz", "text_ru", "text_en", "is_correct")
        labels = {
            "question": _("Question"),
            "text": _("Default answer"),
            "text_uz": _("Answer (Uzbek)"),
            "text_ru": _("Answer (Russian)"),
            "text_en": _("Answer (English)"),
            "is_correct": _("Correct answer"),
        }
