from rest_framework import serializers
from .models import Category, Course, Lesson, LessonAttachment, Enrollment


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name', 'slug', 'icon')


class LessonAttachmentSerializer(serializers.ModelSerializer):
    file = serializers.SerializerMethodField()

    def get_file(self, obj):
        return f'/api/videos/attachments/{obj.pk}/'

    class Meta:
        model = LessonAttachment
        fields = ('id', 'title', 'file', 'file_type')


class LessonListSerializer(serializers.ModelSerializer):
    is_completed = serializers.SerializerMethodField()
    watched_seconds = serializers.SerializerMethodField()

    class Meta:
        model = Lesson
        fields = (
            'id', 'title', 'order', 'duration_seconds',
            'is_free_preview', 'is_completed', 'watched_seconds', 'thumbnail',
        )

    def get_is_completed(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            cached = getattr(obj, 'viewer_progresses', None)
            return any(p.is_completed for p in cached) if cached is not None else obj.progresses.filter(user=request.user, is_completed=True).exists()
        return False

    def get_watched_seconds(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            cached = getattr(obj, 'viewer_progresses', None)
            progress = (cached[0] if cached else None) if cached is not None else obj.progresses.filter(user=request.user).first()
            return progress.watched_seconds if progress else 0
        return 0


class LessonDetailSerializer(LessonListSerializer):
    attachments = LessonAttachmentSerializer(many=True, read_only=True)
    course_slug = serializers.CharField(source='course.slug', read_only=True)
    course_title = serializers.CharField(source='course.title', read_only=True)
    video_status = serializers.SerializerMethodField()

    class Meta(LessonListSerializer.Meta):
        fields = LessonListSerializer.Meta.fields + ('description', 'attachments', 'video_status', 'course_slug', 'course_title')

    def get_video_status(self, obj):
        if hasattr(obj, 'video'):
            return obj.video.status
        return None


class CourseListSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    total_lessons = serializers.IntegerField(source='published_lesson_count', read_only=True)
    progress = serializers.SerializerMethodField()
    is_enrolled = serializers.SerializerMethodField()
    is_wishlisted = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    reviews_count = serializers.IntegerField(source='review_count', read_only=True)

    class Meta:
        model = Course
        fields = (
            'id', 'title', 'slug', 'description', 'thumbnail',
            'category', 'instructor', 'total_lessons',
            'progress', 'is_enrolled', 'is_wishlisted',
            'average_rating', 'reviews_count',
        )

    def get_average_rating(self, obj):
        return round(obj.review_average or 0, 1)

    def get_is_wishlisted(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return bool(obj.viewer_wishlist)
        return False

    def get_progress(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            if obj.viewer_enrollments:
                lessons = obj.published_lessons
                completed = sum(any(p.is_completed for p in lesson.viewer_progresses) for lesson in lessons)
                return round(completed / len(lessons) * 100) if lessons else 0
        return 0

    def get_is_enrolled(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return bool(obj.viewer_enrollments)
        return False


class CourseDetailSerializer(CourseListSerializer):
    lessons = serializers.SerializerMethodField()

    class Meta(CourseListSerializer.Meta):
        fields = CourseListSerializer.Meta.fields + ('lessons',)

    def get_lessons(self, obj):
        request = self.context.get('request')
        lessons = getattr(obj, 'published_lessons', None)
        if lessons is None:
            lessons = obj.lessons.filter(is_published=True).order_by('order')
        return LessonListSerializer(lessons, many=True, context={'request': request}).data


class EnrollmentSerializer(serializers.ModelSerializer):
    course_title = serializers.CharField(source='course.title', read_only=True)
    progress = serializers.SerializerMethodField()

    class Meta:
        model = Enrollment
        fields = ('id', 'course', 'course_title', 'progress', 'enrolled_at')
        read_only_fields = ('enrolled_at',)

    def get_progress(self, obj):
        return obj.get_progress()
