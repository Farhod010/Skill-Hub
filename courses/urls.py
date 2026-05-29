from django.urls import path

from .views import (
    CourseDetailView,
    CourseListView,
    LessonWatchView,
    add_lesson_comment,
    certificate_download,
    certificate_detail,
    delete_review,
    enroll_in_course,
    mark_lesson_completed,
    quiz_result_detail,
    save_watch_progress,
    submit_review,
    take_quiz,
    toggle_wishlist,
)

app_name = "courses"

urlpatterns = [
    path("", CourseListView.as_view(), name="course_list"),
    path("<slug:slug>/", CourseDetailView.as_view(), name="course_detail"),
    path("<slug:slug>/enroll/", enroll_in_course, name="course_enroll"),
    path("<slug:slug>/wishlist/", toggle_wishlist, name="course_wishlist"),
    path("<slug:slug>/review/", submit_review, name="course_review"),
    path("<slug:slug>/review/delete/", delete_review, name="course_review_delete"),
    path("<slug:slug>/quiz/<int:quiz_id>/", take_quiz, name="quiz_take"),
    path("<slug:slug>/quiz-results/<int:result_id>/", quiz_result_detail, name="quiz_result"),
    path("<slug:slug>/certificate/", certificate_detail, name="certificate_detail"),
    path("<slug:slug>/certificate/download/", certificate_download, name="certificate_download"),
    path(
        "<slug:course_slug>/lessons/<int:lesson_id>/",
        LessonWatchView.as_view(),
        name="lesson_watch",
    ),
    path(
        "<slug:course_slug>/lessons/<int:lesson_id>/progress/",
        save_watch_progress,
        name="lesson_progress",
    ),
    path(
        "<slug:course_slug>/lessons/<int:lesson_id>/complete/",
        mark_lesson_completed,
        name="lesson_complete",
    ),
    path(
        "<slug:course_slug>/lessons/<int:lesson_id>/comment/",
        add_lesson_comment,
        name="lesson_comment",
    ),
]
