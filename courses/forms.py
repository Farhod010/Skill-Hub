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
            "short_description",
            "short_description_uz",
            "short_description_ru",
            "short_description_en",
            "full_description",
            "description_uz",
            "description_ru",
            "description_en",
            "price",
            "discount_percent",
            "level",
            "language",
            "status",
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

    def clean_instructor(self):
        instructor = self.cleaned_data.get("instructor") or getattr(self, "actor", None)
        if instructor.role not in {User.Roles.INSTRUCTOR, User.Roles.ADMIN}:
            raise ValidationError(_("Only instructors or admins can be assigned to a course."))
        return instructor


class SectionForm(StyledModelForm):
    def __init__(self, *args, actor=None, **kwargs):
        super().__init__(*args, **kwargs)
        if actor and getattr(actor, "role", None) == User.Roles.INSTRUCTOR and not actor.can_access_panel:
            self.fields["course"].queryset = Course.objects.filter(instructor=actor).order_by("title")

    class Meta:
        model = Section
        fields = ("course", "title", "description", "order_index")
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
        }


class LessonForm(StyledModelForm):
    def __init__(self, *args, actor=None, **kwargs):
        super().__init__(*args, **kwargs)
        if actor and getattr(actor, "role", None) == User.Roles.INSTRUCTOR and not actor.can_access_panel:
            self.fields["section"].queryset = Section.objects.filter(course__instructor=actor).order_by(
                "course__title",
                "order_index",
            )

    class Meta:
        model = Lesson
        fields = (
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

    def clean(self):
        cleaned_data = super().clean()
        video_file = cleaned_data.get("video_file")
        video_url = (cleaned_data.get("video_url") or "").strip()
        if not video_file and not video_url:
            raise ValidationError(_("Add either an uploaded video file or an external video URL."))
        return cleaned_data


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
        fields = ("course", "title", "description", "pass_percent", "is_active")
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
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
        fields = ("quiz", "prompt", "order_index")
        widgets = {
            "prompt": forms.Textarea(attrs={"rows": 4}),
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
        fields = ("question", "text", "is_correct")
