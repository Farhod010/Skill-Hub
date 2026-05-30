from django.urls import path

from .views import (
    student_dashboard,
    teacher_course_delete,
    teacher_course_list,
    teacher_course_create,
    teacher_course_edit,
    teacher_dashboard,
    teacher_earnings,
    teacher_lesson_delete,
    teacher_lesson_edit,
    teacher_lesson_list,
    teacher_lesson_create,
    teacher_password_change,
    teacher_profile_edit,
    teacher_question_create,
    teacher_quiz_create,
    teacher_review_list,
    teacher_student_list,
)

app_name = "dashboard"

urlpatterns = [
    path("", student_dashboard, name="student_dashboard"),
    path("teacher/", teacher_dashboard, name="teacher_dashboard"),
    path("teacher/courses/", teacher_course_list, name="teacher_course_list"),
    path("teacher/courses/create/", teacher_course_create, name="teacher_course_create"),
    path("teacher/courses/<int:pk>/edit/", teacher_course_edit, name="teacher_course_edit"),
    path("teacher/courses/<int:pk>/delete/", teacher_course_delete, name="teacher_course_delete"),
    path("teacher/courses/<int:course_id>/lessons/", teacher_lesson_list, name="teacher_lesson_list"),
    path("teacher/lessons/create/", teacher_lesson_create, name="teacher_lesson_create"),
    path("teacher/lessons/<int:pk>/edit/", teacher_lesson_edit, name="teacher_lesson_edit"),
    path("teacher/lessons/<int:pk>/delete/", teacher_lesson_delete, name="teacher_lesson_delete"),
    path("teacher/quizzes/create/", teacher_quiz_create, name="teacher_quiz_create"),
    path("teacher/quizzes/<int:quiz_id>/questions/create/", teacher_question_create, name="teacher_question_create"),
    path("teacher/students/", teacher_student_list, name="teacher_student_list"),
    path("teacher/reviews/", teacher_review_list, name="teacher_review_list"),
    path("teacher/earnings/", teacher_earnings, name="teacher_earnings"),
    path("teacher/profile/", teacher_profile_edit, name="teacher_profile"),
    path("teacher/profile/password/", teacher_password_change, name="teacher_password_change"),
]
