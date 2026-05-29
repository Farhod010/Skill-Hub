from django.db.models import Q
from rest_framework import permissions, viewsets

from accounts.models import User
from courses.models import Category, Course, Enrollment, Lesson, Review, Section, WatchProgress, Wishlist
from payments.models import Payment
from site_settings.models import SiteSetting

from .permissions import AllowCreateOrPanelOnly, IsAuthenticatedNotBlocked, IsPanelUserOrReadOnly
from .serializers import (
    CategorySerializer,
    CourseSerializer,
    EnrollmentSerializer,
    LessonSerializer,
    PaymentSerializer,
    ReviewSerializer,
    SectionSerializer,
    SiteSettingSerializer,
    UserSerializer,
    WatchProgressSerializer,
    WishlistSerializer,
)


class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    search_fields = ("email", "username", "first_name", "last_name", "role")
    filterset_fields = ("role", "is_active", "is_blocked")
    ordering_fields = ("date_joined", "email", "first_name")
    ordering = ("-date_joined",)

    def get_queryset(self):
        queryset = User.objects.all().order_by("-date_joined")
        if self.request.user.is_authenticated and self.request.user.can_access_panel:
            return queryset
        if self.request.user.is_authenticated:
            return queryset.filter(pk=self.request.user.pk)
        return queryset.none()

    def get_permissions(self):
        if self.action == "create":
            return [permissions.AllowAny()]
        return [IsAuthenticatedNotBlocked()]

    def perform_create(self, serializer):
        serializer.save(
            role=User.Roles.STUDENT,
            is_active=True,
            is_blocked=False,
            is_staff=False,
            is_superuser=False,
        )


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all().order_by("title")
    serializer_class = CategorySerializer
    permission_classes = [IsPanelUserOrReadOnly]
    search_fields = ("title", "description")
    filterset_fields = ("is_active",)
    ordering_fields = ("title", "created_at")
    ordering = ("title",)

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.is_authenticated and self.request.user.can_access_panel:
            return queryset
        return queryset.filter(is_active=True)


class CourseViewSet(viewsets.ModelViewSet):
    serializer_class = CourseSerializer
    permission_classes = [IsPanelUserOrReadOnly]
    search_fields = (
        "title",
        "short_description",
        "full_description",
        "category__title",
        "instructor__email",
    )
    filterset_fields = ("category", "level", "language", "is_published", "is_featured", "instructor")
    ordering_fields = ("created_at", "price", "title", "updated_at")
    ordering = ("-created_at",)

    def get_queryset(self):
        queryset = Course.objects.select_related("category", "instructor").all()
        user = self.request.user
        if user.is_authenticated and user.can_access_panel:
            return queryset
        if user.is_authenticated:
            return queryset.filter(Q(is_published=True) | Q(instructor=user)).distinct()
        return queryset.filter(is_published=True)


class SectionViewSet(viewsets.ModelViewSet):
    serializer_class = SectionSerializer
    permission_classes = [IsPanelUserOrReadOnly]
    search_fields = ("title", "description", "course__title")
    filterset_fields = ("course",)
    ordering_fields = ("course__title", "order_index", "title")
    ordering = ("course__title", "order_index")

    def get_queryset(self):
        queryset = Section.objects.select_related("course").all()
        user = self.request.user
        if user.is_authenticated and user.can_access_panel:
            return queryset
        if user.is_authenticated:
            return queryset.filter(Q(course__is_published=True) | Q(course__instructor=user)).distinct()
        return queryset.filter(course__is_published=True)


class LessonViewSet(viewsets.ModelViewSet):
    serializer_class = LessonSerializer
    permission_classes = [IsPanelUserOrReadOnly]
    search_fields = ("title", "description", "section__title", "section__course__title")
    filterset_fields = ("section", "is_preview", "section__course")
    ordering_fields = ("section__course__title", "section__order_index", "order_index", "title")
    ordering = ("section__course__title", "section__order_index", "order_index")

    def get_queryset(self):
        queryset = Lesson.objects.select_related("section", "section__course").all()
        user = self.request.user
        if user.is_authenticated and user.can_access_panel:
            return queryset
        if user.is_authenticated:
            return queryset.filter(
                Q(is_preview=True, section__course__is_published=True)
                | Q(section__course__enrollments__student=user)
                | Q(section__course__instructor=user)
            ).distinct()
        return queryset.filter(is_preview=True, section__course__is_published=True)


class EnrollmentViewSet(viewsets.ModelViewSet):
    serializer_class = EnrollmentSerializer
    permission_classes = [IsAuthenticatedNotBlocked]
    search_fields = ("student__email", "course__title")
    filterset_fields = ("course", "student")
    ordering_fields = ("enrolled_at", "price_paid")
    ordering = ("-enrolled_at",)

    def get_queryset(self):
        queryset = Enrollment.objects.select_related("student", "course", "course__category", "course__instructor")
        if self.request.user.can_access_panel:
            return queryset
        return queryset.filter(student=self.request.user)

    def perform_create(self, serializer):
        if self.request.user.can_access_panel and serializer.validated_data.get("student"):
            course = serializer.validated_data["course"]
            serializer.save(price_paid=serializer.validated_data.get("price_paid") or course.price)
            return
        course = serializer.validated_data["course"]
        serializer.save(student=self.request.user, price_paid=serializer.validated_data.get("price_paid") or course.price)


class WishlistViewSet(viewsets.ModelViewSet):
    serializer_class = WishlistSerializer
    permission_classes = [IsAuthenticatedNotBlocked]
    search_fields = ("student__email", "course__title")
    filterset_fields = ("course", "student")
    ordering_fields = ("created_at",)
    ordering = ("-created_at",)

    def get_queryset(self):
        queryset = Wishlist.objects.select_related("student", "course", "course__category", "course__instructor")
        if self.request.user.can_access_panel:
            return queryset
        return queryset.filter(student=self.request.user)

    def perform_create(self, serializer):
        if self.request.user.can_access_panel and serializer.validated_data.get("student"):
            serializer.save()
            return
        serializer.save(student=self.request.user)


class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    search_fields = ("course__title", "student__email", "title", "comment")
    filterset_fields = ("course", "student", "rating", "is_approved")
    ordering_fields = ("created_at", "rating", "updated_at")
    ordering = ("-created_at",)

    def get_permissions(self):
        if self.action in {"list", "retrieve"}:
            return [permissions.AllowAny()]
        return [IsAuthenticatedNotBlocked()]

    def get_queryset(self):
        queryset = Review.objects.select_related("student", "course", "course__category", "course__instructor")
        user = self.request.user
        if user.is_authenticated and user.can_access_panel:
            return queryset
        if user.is_authenticated:
            return queryset.filter(Q(is_approved=True) | Q(student=user)).distinct()
        return queryset.filter(is_approved=True)

    def perform_create(self, serializer):
        if self.request.user.can_access_panel and serializer.validated_data.get("student"):
            serializer.save()
            return
        serializer.save(student=self.request.user, is_approved=False)


class WatchProgressViewSet(viewsets.ModelViewSet):
    serializer_class = WatchProgressSerializer
    permission_classes = [IsAuthenticatedNotBlocked]
    search_fields = ("student__email", "lesson__title", "lesson__section__course__title")
    filterset_fields = ("student", "lesson", "completed")
    ordering_fields = ("last_watched_at", "watched_seconds", "completed_at")
    ordering = ("-last_watched_at",)

    def get_queryset(self):
        queryset = WatchProgress.objects.select_related(
            "student", "lesson", "lesson__section", "lesson__section__course"
        )
        if self.request.user.can_access_panel:
            return queryset
        return queryset.filter(student=self.request.user)

    def perform_create(self, serializer):
        if self.request.user.can_access_panel and serializer.validated_data.get("student"):
            serializer.save()
            return
        serializer.save(student=self.request.user)


class PaymentViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentSerializer
    search_fields = ("reference", "user__email", "course__title")
    filterset_fields = ("status", "provider", "course", "user")
    ordering_fields = ("created_at", "amount", "updated_at")
    ordering = ("-created_at",)

    def get_permissions(self):
        if self.action in {"list", "retrieve"}:
            return [IsAuthenticatedNotBlocked()]
        return [IsPanelUserOrReadOnly()]

    def get_queryset(self):
        queryset = Payment.objects.select_related("user", "course", "enrollment")
        if self.request.user.can_access_panel:
            return queryset
        return queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save()


class SiteSettingViewSet(viewsets.ModelViewSet):
    queryset = SiteSetting.objects.all()
    serializer_class = SiteSettingSerializer
    permission_classes = [IsPanelUserOrReadOnly]
    search_fields = ("site_name", "contact_email", "footer_text")
    filterset_fields = ()
    ordering_fields = ("updated_at", "site_name")
    ordering = ("site_name",)
