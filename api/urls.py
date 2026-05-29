from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    CategoryViewSet,
    CourseViewSet,
    EnrollmentViewSet,
    LessonViewSet,
    PaymentViewSet,
    ReviewViewSet,
    SectionViewSet,
    SiteSettingViewSet,
    UserViewSet,
    WatchProgressViewSet,
    WishlistViewSet,
)

app_name = "api"

router = DefaultRouter()
router.register("users", UserViewSet, basename="users")
router.register("categories", CategoryViewSet, basename="categories")
router.register("courses", CourseViewSet, basename="courses")
router.register("sections", SectionViewSet, basename="sections")
router.register("lessons", LessonViewSet, basename="lessons")
router.register("enrollments", EnrollmentViewSet, basename="enrollments")
router.register("wishlist", WishlistViewSet, basename="wishlist")
router.register("reviews", ReviewViewSet, basename="reviews")
router.register("watch-progress", WatchProgressViewSet, basename="watch-progress")
router.register("payments", PaymentViewSet, basename="payments")
router.register("site-settings", SiteSettingViewSet, basename="site-settings")

urlpatterns = [
    path("", include(router.urls)),
    path("auth/", include("rest_framework.urls")),
]
