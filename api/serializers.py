from rest_framework import serializers

from accounts.models import User
from courses.models import (
    Category,
    Course,
    Enrollment,
    Lesson,
    Review,
    Section,
    WatchProgress,
    Wishlist,
)
from payments.models import Payment
from site_settings.models import SiteSetting


class UserMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "email", "username", "first_name", "last_name", "role")


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "phone",
            "role",
            "avatar",
            "bio",
            "is_blocked",
            "is_active",
            "password",
            "date_joined",
        )
        read_only_fields = ("date_joined",)

    def get_fields(self):
        fields = super().get_fields()
        request = self.context.get("request")
        user = getattr(request, "user", None)

        protected_fields = ("role", "is_blocked", "is_active")
        if not (user and user.is_authenticated and user.can_access_panel):
            for field_name in protected_fields:
                fields[field_name].read_only = True
        return fields

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        user = User(**validated_data)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = "__all__"


class CourseSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        source="category",
        queryset=Category.objects.all(),
        write_only=True,
    )
    instructor = UserMiniSerializer(read_only=True)
    instructor_id = serializers.PrimaryKeyRelatedField(
        source="instructor",
        queryset=User.objects.filter(role__in=[User.Roles.INSTRUCTOR, User.Roles.ADMIN]),
        write_only=True,
    )
    average_rating = serializers.FloatField(read_only=True)
    review_count = serializers.IntegerField(read_only=True)
    lesson_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Course
        fields = (
            "id",
            "title",
            "slug",
            "category",
            "category_id",
            "instructor",
            "instructor_id",
            "thumbnail",
            "short_description",
            "full_description",
            "price",
            "level",
            "language",
            "is_published",
            "is_featured",
            "created_at",
            "updated_at",
            "average_rating",
            "review_count",
            "lesson_count",
        )
        read_only_fields = ("created_at", "updated_at")


class SectionSerializer(serializers.ModelSerializer):
    course = CourseSerializer(read_only=True)
    course_id = serializers.PrimaryKeyRelatedField(
        source="course",
        queryset=Course.objects.all(),
        write_only=True,
    )

    class Meta:
        model = Section
        fields = ("id", "course", "course_id", "title", "description", "order_index")


class LessonSerializer(serializers.ModelSerializer):
    section = SectionSerializer(read_only=True)
    section_id = serializers.PrimaryKeyRelatedField(
        source="section",
        queryset=Section.objects.all(),
        write_only=True,
    )
    player = serializers.SerializerMethodField()

    class Meta:
        model = Lesson
        fields = (
            "id",
            "section",
            "section_id",
            "title",
            "description",
            "video_file",
            "video_url",
            "duration_minutes",
            "is_preview",
            "order_index",
            "created_at",
            "updated_at",
            "player",
        )
        read_only_fields = ("created_at", "updated_at", "player")

    def get_player(self, obj):
        return obj.get_player_data()


class EnrollmentSerializer(serializers.ModelSerializer):
    student = UserMiniSerializer(read_only=True)
    student_id = serializers.PrimaryKeyRelatedField(
        source="student",
        queryset=User.objects.all(),
        write_only=True,
        required=False,
    )
    course = CourseSerializer(read_only=True)
    course_id = serializers.PrimaryKeyRelatedField(
        source="course",
        queryset=Course.objects.all(),
        write_only=True,
    )

    class Meta:
        model = Enrollment
        fields = (
            "id",
            "student",
            "student_id",
            "course",
            "course_id",
            "price_paid",
            "enrolled_at",
        )
        read_only_fields = ("enrolled_at",)


class WishlistSerializer(serializers.ModelSerializer):
    student = UserMiniSerializer(read_only=True)
    student_id = serializers.PrimaryKeyRelatedField(
        source="student",
        queryset=User.objects.all(),
        write_only=True,
        required=False,
    )
    course = CourseSerializer(read_only=True)
    course_id = serializers.PrimaryKeyRelatedField(
        source="course",
        queryset=Course.objects.all(),
        write_only=True,
    )

    class Meta:
        model = Wishlist
        fields = ("id", "student", "student_id", "course", "course_id", "created_at")
        read_only_fields = ("created_at",)


class ReviewSerializer(serializers.ModelSerializer):
    student = UserMiniSerializer(read_only=True)
    student_id = serializers.PrimaryKeyRelatedField(
        source="student",
        queryset=User.objects.all(),
        write_only=True,
        required=False,
    )
    course = CourseSerializer(read_only=True)
    course_id = serializers.PrimaryKeyRelatedField(
        source="course",
        queryset=Course.objects.all(),
        write_only=True,
    )

    class Meta:
        model = Review
        fields = (
            "id",
            "student",
            "student_id",
            "course",
            "course_id",
            "rating",
            "title",
            "comment",
            "is_approved",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("created_at", "updated_at")


class WatchProgressSerializer(serializers.ModelSerializer):
    student = UserMiniSerializer(read_only=True)
    student_id = serializers.PrimaryKeyRelatedField(
        source="student",
        queryset=User.objects.all(),
        write_only=True,
        required=False,
    )
    lesson = LessonSerializer(read_only=True)
    lesson_id = serializers.PrimaryKeyRelatedField(
        source="lesson",
        queryset=Lesson.objects.all(),
        write_only=True,
    )

    class Meta:
        model = WatchProgress
        fields = (
            "id",
            "student",
            "student_id",
            "lesson",
            "lesson_id",
            "watched_seconds",
            "completed",
            "completed_at",
            "last_watched_at",
        )
        read_only_fields = ("completed_at", "last_watched_at")


class PaymentSerializer(serializers.ModelSerializer):
    user = UserMiniSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        source="user",
        queryset=User.objects.all(),
        write_only=True,
        required=False,
    )
    course = CourseSerializer(read_only=True)
    course_id = serializers.PrimaryKeyRelatedField(
        source="course",
        queryset=Course.objects.all(),
        write_only=True,
    )
    enrollment_id = serializers.PrimaryKeyRelatedField(
        source="enrollment",
        queryset=Enrollment.objects.all(),
        write_only=True,
        allow_null=True,
        required=False,
    )

    class Meta:
        model = Payment
        fields = (
            "id",
            "user",
            "user_id",
            "course",
            "course_id",
            "enrollment_id",
            "amount",
            "provider",
            "reference",
            "status",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("reference", "created_at", "updated_at")


class SiteSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteSetting
        fields = "__all__"
