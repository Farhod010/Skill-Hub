from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.models import User
from courses.models import (
    Answer,
    Certificate,
    Category,
    Course,
    Enrollment,
    Lesson,
    Question,
    Quiz,
    QuizResult,
    Review,
    Section,
    WatchProgress,
    Wishlist,
)
from payments.models import Payment
from site_settings.models import SiteSetting


class Command(BaseCommand):
    help = "Seed demo content for the SkillHub platform."

    @transaction.atomic
    def handle(self, *args, **options):
        admin_user, _ = User.objects.update_or_create(
            email="admin@skillhub.local",
            defaults={
                "username": "admin",
                "first_name": "SkillHub",
                "last_name": "Admin",
                "role": User.Roles.ADMIN,
                "is_staff": True,
                "is_superuser": True,
                "is_active": True,
            },
        )
        admin_user.set_password("admin12345")
        admin_user.save()

        instructor_user, _ = User.objects.update_or_create(
            email="instructor@skillhub.local",
            defaults={
                "username": "instructor",
                "first_name": "Amina",
                "last_name": "Khan",
                "role": User.Roles.INSTRUCTOR,
                "is_staff": False,
                "is_active": True,
                "phone": "+998900001111",
                "bio": "Product-minded educator focused on practical digital skills.",
            },
        )
        instructor_user.set_password("instructor12345")
        instructor_user.save()

        moderator_user, _ = User.objects.update_or_create(
            email="moderator@skillhub.local",
            defaults={
                "username": "moderator",
                "first_name": "Nadia",
                "last_name": "Reed",
                "role": User.Roles.MODERATOR,
                "is_staff": False,
                "is_active": True,
                "bio": "Content moderator keeping courses and reviews in shape.",
            },
        )
        moderator_user.set_password("moderator12345")
        moderator_user.save()

        student_user, _ = User.objects.update_or_create(
            email="student@skillhub.local",
            defaults={
                "username": "student",
                "first_name": "Leo",
                "last_name": "Turner",
                "role": User.Roles.STUDENT,
                "is_staff": False,
                "is_active": True,
                "phone": "+998900002222",
                "bio": "Lifelong learner exploring new tech and creative habits.",
            },
        )
        student_user.set_password("student12345")
        student_user.save()

        blocked_user, _ = User.objects.update_or_create(
            email="blocked@skillhub.local",
            defaults={
                "username": "blocked",
                "first_name": "Blocked",
                "last_name": "Learner",
                "role": User.Roles.STUDENT,
                "is_staff": False,
                "is_active": True,
                "is_blocked": True,
                "bio": "Blocked demo account for authentication checks.",
            },
        )
        blocked_user.set_password("blocked12345")
        blocked_user.save()

        categories = {}
        for title, description in [
            ("Web Development", "Build production-ready applications for the modern web."),
            ("Data Science", "Learn data analysis, modeling, and machine learning workflows."),
            ("Product Design", "Design polished interfaces and thoughtful user experiences."),
        ]:
            category, _ = Category.objects.update_or_create(
                title=title,
                defaults={"description": description, "is_active": True},
            )
            categories[title] = category

        course_specs = [
            {
                "title": "Django from Zero to Deployment",
                "category": categories["Web Development"],
                "price": Decimal("79.00"),
                "level": Course.Levels.BEGINNER,
                "language": "English",
                "is_featured": True,
                "short_description": "Build a complete Django app with auth, PostgreSQL, and polished templates.",
                "full_description": (
                    "A practical, project-based Django course covering app architecture, "
                    "custom users, database modeling, template-driven UI, and deployment thinking."
                ),
                "sections": [
                    (
                        "Foundations",
                        [
                            ("Welcome and platform tour", 8, True, "https://samplelib.com/lib/preview/mp4/sample-10s.mp4"),
                            ("Project structure that scales", 22, False, "https://www.youtube.com/watch?v=rfscVS0vtbw"),
                        ],
                    ),
                    (
                        "Building the product",
                        [
                            ("Custom user authentication", 18, False, "https://samplelib.com/lib/preview/mp4/sample-15s.mp4"),
                            ("Courses, sections, and lessons", 26, False, "https://www.youtube.com/watch?v=jNQXAC9IVRw"),
                        ],
                    ),
                ],
            },
            {
                "title": "Practical Data Storytelling",
                "category": categories["Data Science"],
                "price": Decimal("59.00"),
                "level": Course.Levels.INTERMEDIATE,
                "language": "English",
                "is_featured": True,
                "short_description": "Turn messy data into clear decisions with visuals, metrics, and narrative.",
                "full_description": (
                    "Learn how analysts organize data projects, build confident dashboards, "
                    "and communicate insights that influence product and business decisions."
                ),
                "sections": [
                    (
                        "Story-first analysis",
                        [
                            ("What makes a useful metric", 14, True, "https://samplelib.com/lib/preview/mp4/sample-5s.mp4"),
                            ("Cleaning data for trust", 19, False, "https://www.youtube.com/watch?v=2lAe1cqCOXo"),
                        ],
                    ),
                    (
                        "Presenting insights",
                        [
                            ("Designing decision-ready charts", 21, False, "https://samplelib.com/lib/preview/mp4/sample-20s.mp4"),
                            ("Narrative structure for reports", 17, False, "https://www.youtube.com/watch?v=ysz5S6PUM-U"),
                        ],
                    ),
                ],
            },
            {
                "title": "Premium UI Design Systems",
                "category": categories["Product Design"],
                "price": Decimal("69.00"),
                "level": Course.Levels.ADVANCED,
                "language": "English",
                "is_featured": False,
                "short_description": "Craft elegant component systems, visual language, and scalable design decisions.",
                "full_description": (
                    "Explore typography, spacing, tokens, component strategy, and the "
                    "handoff patterns teams use to keep premium interfaces consistent."
                ),
                "sections": [
                    (
                        "Visual foundations",
                        [
                            ("Building a visual system", 12, True, "https://samplelib.com/lib/preview/mp4/sample-30s.mp4"),
                            ("Tokens, themes, and scale", 24, False, "https://www.youtube.com/watch?v=tgbNymZ7vqY"),
                        ],
                    ),
                    (
                        "Production workflows",
                        [
                            ("Designing reusable components", 28, False, "https://samplelib.com/lib/preview/mp4/sample-15s.mp4"),
                            ("Review rituals with engineers", 16, False, "https://www.youtube.com/watch?v=aqz-KE-bpKQ"),
                        ],
                    ),
                ],
            },
            {
                "title": "Learning Sprints for Busy Teams",
                "category": categories["Product Design"],
                "price": Decimal("0.00"),
                "level": Course.Levels.BEGINNER,
                "language": "English",
                "is_featured": True,
                "short_description": "A free mini-course on structuring short, sustainable learning habits for teams.",
                "full_description": (
                    "A short free course that shows how to organize weekly learning sprints, "
                    "reflect on progress, and keep momentum without burning out."
                ),
                "sections": [
                    (
                        "Sprint setup",
                        [
                            ("Why short learning cycles work", 9, True, "https://samplelib.com/lib/preview/mp4/sample-10s.mp4"),
                            ("Choosing a weekly focus", 11, False, "https://samplelib.com/lib/preview/mp4/sample-15s.mp4"),
                        ],
                    ),
                    (
                        "Keeping momentum",
                        [
                            ("Running a retro on your learning", 10, False, "https://www.youtube.com/watch?v=ysz5S6PUM-U"),
                            ("Sharing outcomes with your team", 13, False, "https://samplelib.com/lib/preview/mp4/sample-20s.mp4"),
                        ],
                    ),
                ],
            },
        ]

        created_courses = []
        for spec in course_specs:
            course, _ = Course.objects.update_or_create(
                title=spec["title"],
                defaults={
                    "category": spec["category"],
                    "instructor": instructor_user,
                    "price": spec["price"],
                    "discount_percent": 10 if spec["price"] else 0,
                    "level": spec["level"],
                    "language": spec["language"],
                    "short_description": spec["short_description"],
                    "full_description": spec["full_description"],
                    "status": Course.Statuses.ACTIVE,
                    "is_published": True,
                    "is_featured": spec["is_featured"],
                    "certificate_enabled": True,
                },
            )
            created_courses.append(course)

            for section_index, (section_title, lessons) in enumerate(spec["sections"], start=1):
                section, _ = Section.objects.update_or_create(
                    course=course,
                    order_index=section_index,
                    defaults={
                        "title": section_title,
                        "description": f"{section_title} for {course.title}.",
                    },
                )
                for lesson_index, (lesson_title, duration, preview, video_url) in enumerate(
                    lessons, start=1
                ):
                    Lesson.objects.update_or_create(
                        section=section,
                        order_index=lesson_index,
                        defaults={
                            "title": lesson_title,
                            "description": f"Lesson notes for {lesson_title}.",
                            "duration_minutes": duration,
                            "is_preview": preview,
                            "video_url": video_url,
                        },
                        )

            quiz, _ = Quiz.objects.update_or_create(
                course=course,
                title=f"{course.title} Final Quiz",
                defaults={
                    "description": f"Final knowledge check for {course.title}.",
                    "pass_percent": 70,
                    "is_active": True,
                },
            )
            question, _ = Question.objects.update_or_create(
                quiz=quiz,
                order_index=1,
                defaults={"prompt": f"What is the main focus of {course.title}?"},
            )
            Answer.objects.update_or_create(
                question=question,
                text="Practical application and structured progress",
                defaults={"is_correct": True},
            )
            Answer.objects.update_or_create(
                question=question,
                text="Only theoretical memorization",
                defaults={"is_correct": False},
            )

        primary_course = created_courses[0]
        secondary_course = created_courses[1]

        first_enrollment, _ = Enrollment.objects.update_or_create(
            student=student_user,
            course=primary_course,
            defaults={"price_paid": primary_course.price},
        )
        second_enrollment, _ = Enrollment.objects.update_or_create(
            student=student_user,
            course=secondary_course,
            defaults={"price_paid": secondary_course.price},
        )

        Payment.objects.update_or_create(
            enrollment=first_enrollment,
            defaults={
                "user": student_user,
                "course": primary_course,
                "amount": primary_course.price,
                "provider": "manual",
                "status": Payment.Status.COMPLETED,
            },
        )
        Payment.objects.update_or_create(
            enrollment=second_enrollment,
            defaults={
                "user": student_user,
                "course": secondary_course,
                "amount": secondary_course.price,
                "provider": "manual",
                "status": Payment.Status.COMPLETED,
            },
        )

        wishlist_course = next((course for course in created_courses if course.is_free), created_courses[2])
        Wishlist.objects.get_or_create(student=student_user, course=wishlist_course)

        first_lesson = primary_course.first_lesson
        second_lesson = (
            Lesson.objects.filter(section__course=primary_course)
            .exclude(pk=first_lesson.pk if first_lesson else None)
            .order_by("section__order_index", "order_index")
            .first()
        )
        if first_lesson:
            WatchProgress.objects.update_or_create(
                student=student_user,
                lesson=first_lesson,
                defaults={
                    "watched_seconds": first_lesson.duration_seconds,
                    "completed": True,
                },
            )
        if second_lesson:
            WatchProgress.objects.update_or_create(
                student=student_user,
                lesson=second_lesson,
                defaults={
                    "watched_seconds": min(420, second_lesson.duration_seconds),
                    "completed": False,
                },
            )

        free_course = next((course for course in created_courses if course.is_free), None)
        if free_course:
            Enrollment.objects.update_or_create(
                student=student_user,
                course=free_course,
                defaults={"price_paid": free_course.final_price},
            )
            for lesson in Lesson.objects.filter(section__course=free_course):
                WatchProgress.objects.update_or_create(
                    student=student_user,
                    lesson=lesson,
                    defaults={
                        "watched_seconds": lesson.duration_seconds,
                        "completed": True,
                    },
                )
            quiz = free_course.quizzes.first()
            if quiz:
                quiz_result, _ = QuizResult.objects.update_or_create(
                    student=student_user,
                    quiz=quiz,
                    defaults={
                        "score": quiz.question_count,
                        "total_questions": quiz.question_count,
                        "passed": True,
                    },
                )
                Certificate.objects.update_or_create(
                    student=student_user,
                    course=free_course,
                    defaults={"quiz_result": quiz_result},
                )

        Review.objects.update_or_create(
            student=student_user,
            course=primary_course,
            defaults={
                "rating": 5,
                "title": "Clear, practical, and motivating",
                "comment": "This course felt like building with a great mentor beside me the whole way.",
                "is_approved": True,
            },
        )
        Review.objects.update_or_create(
            student=admin_user,
            course=secondary_course,
            defaults={
                "rating": 4,
                "title": "Useful frameworks for modern analytics",
                "comment": "Strong structure and very actionable examples for communicating insights.",
                "is_approved": True,
            },
        )

        settings_obj = SiteSetting.get_solo()
        settings_obj.site_name = "SkillHub"
        settings_obj.primary_color = "#11324d"
        settings_obj.accent_color = "#d97706"
        settings_obj.footer_text = "SkillHub helps ambitious learners turn momentum into mastery."
        settings_obj.contact_email = "support@skillhub.local"
        settings_obj.smtp_host = "smtp.skillhub.local"
        settings_obj.smtp_port = 587
        settings_obj.smtp_username = "mailer@skillhub.local"
        settings_obj.smtp_password = "demo-password"
        settings_obj.smtp_use_tls = True
        settings_obj.save()

        self.stdout.write(self.style.SUCCESS("SkillHub demo data seeded successfully."))
