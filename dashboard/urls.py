from django.urls import path

from .views import (
    student_dashboard,
    teacher_course_create,
    teacher_course_edit,
    teacher_dashboard,
    teacher_lesson_create,
    teacher_question_create,
    teacher_quiz_create,
)

app_name = "dashboard"

urlpatterns = [
    path("", student_dashboard, name="student_dashboard"),
    path("teacher/", teacher_dashboard, name="teacher_dashboard"),
    path("teacher/courses/create/", teacher_course_create, name="teacher_course_create"),
    path("teacher/courses/<int:pk>/edit/", teacher_course_edit, name="teacher_course_edit"),
    path("teacher/lessons/create/", teacher_lesson_create, name="teacher_lesson_create"),
    path("teacher/quizzes/create/", teacher_quiz_create, name="teacher_quiz_create"),
    path("teacher/quizzes/<int:quiz_id>/questions/create/", teacher_question_create, name="teacher_question_create"),
]
