from rest_framework import serializers
from .models import Wishlist, Review, LessonComment, Question, Answer, Certificate


class WishlistSerializer(serializers.ModelSerializer):
    course_title = serializers.CharField(source='course.title', read_only=True)
    course_slug = serializers.CharField(source='course.slug', read_only=True)
    course_thumbnail = serializers.ImageField(source='course.thumbnail', read_only=True)

    class Meta:
        model = Wishlist
        fields = ('id', 'course', 'course_title', 'course_slug', 'course_thumbnail', 'created_at')
        read_only_fields = ('created_at',)


class ReviewSerializer(serializers.ModelSerializer):
    rating = serializers.IntegerField(min_value=1, max_value=5)

    user_name = serializers.CharField(source='user.full_name', read_only=True)
    user_avatar = serializers.ImageField(source='user.avatar', read_only=True)

    class Meta:
        model = Review
        fields = ('id', 'course', 'user_name', 'user_avatar', 'rating', 'comment', 'created_at')
        read_only_fields = ('created_at',)


class LessonCommentSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    user_avatar = serializers.ImageField(source='user.avatar', read_only=True)
    is_admin = serializers.BooleanField(source='user.is_staff', read_only=True)
    replies_count = serializers.SerializerMethodField()

    class Meta:
        model = LessonComment
        fields = ('id', 'lesson', 'parent', 'user_name', 'user_avatar', 'is_admin',
                  'content', 'replies_count', 'created_at')
        read_only_fields = ('lesson', 'created_at')

    def validate_parent(self, value):
        if value and value.lesson_id != self.context['view'].kwargs['lesson_id']:
            raise serializers.ValidationError('Javob shu dars izohiga tegishli bo‘lishi kerak.')
        return value

    def get_replies_count(self, obj):
        return obj.replies.count()


class AnswerSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.full_name', read_only=True)
    author_avatar = serializers.ImageField(source='author.avatar', read_only=True)

    class Meta:
        model = Answer
        fields = ('id', 'question', 'author_name', 'author_avatar', 'content',
                  'is_admin_answer', 'created_at')
        read_only_fields = ('is_admin_answer', 'created_at')


class QuestionSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    user_avatar = serializers.ImageField(source='user.avatar', read_only=True)
    answers = AnswerSerializer(many=True, read_only=True)
    answers_count = serializers.SerializerMethodField()

    class Meta:
        model = Question
        fields = ('id', 'lesson', 'course', 'user_name', 'user_avatar',
                  'title', 'content', 'status', 'answers', 'answers_count', 'created_at')
        read_only_fields = ('status', 'created_at')

    def get_answers_count(self, obj):
        return obj.answers.count()


class CertificateSerializer(serializers.ModelSerializer):
    course_title = serializers.CharField(source='course.title', read_only=True)
    user_name = serializers.CharField(source='user.full_name', read_only=True)

    class Meta:
        model = Certificate
        fields = ('id', 'certificate_number', 'course', 'course_title',
                  'user_name', 'issued_at')
        read_only_fields = ('certificate_number', 'issued_at')
