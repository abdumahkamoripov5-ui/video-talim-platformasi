import hmac
import hashlib
import time
from django.conf import settings
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from .models import Category, Course, Lesson, Enrollment
from .serializers import (
    CategorySerializer, CourseListSerializer, CourseDetailSerializer,
    LessonDetailSerializer, EnrollmentSerializer,
)


class IsSubscribedOrFreePreview(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if obj.is_free_preview:
            return True
        return request.user.is_authenticated and request.user.has_active_subscription


class CategoryListView(generics.ListAPIView):
    queryset = Category.objects.order_by('name', 'pk')
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]


def catalog_queryset(request):
    from django.db.models import Count, Avg, Q, Prefetch
    from users.models import VideoProgress
    qs = Course.objects.filter(is_published=True).select_related('category').annotate(
        published_lesson_count=Count('lessons', filter=Q(lessons__is_published=True), distinct=True),
        review_average=Avg('reviews__rating', filter=Q(reviews__is_published=True)),
        review_count=Count('reviews', filter=Q(reviews__is_published=True), distinct=True),
    ).order_by('order', '-created_at', 'pk')
    if request.user.is_authenticated:
        qs = qs.prefetch_related(
            Prefetch('enrollments', queryset=Enrollment.objects.filter(user=request.user), to_attr='viewer_enrollments'),
            Prefetch('wishlisted_by', queryset=request.user.wishlist.all(), to_attr='viewer_wishlist'),
            Prefetch('lessons', queryset=Lesson.objects.filter(is_published=True).prefetch_related(
                Prefetch('progresses', queryset=VideoProgress.objects.filter(user=request.user), to_attr='viewer_progresses')
            ), to_attr='published_lessons'),
        )
    return qs


class CourseListView(generics.ListAPIView):
    serializer_class = CourseListSerializer
    permission_classes = [permissions.AllowAny]
    search_fields = ['title', 'description', 'instructor']
    filterset_fields = ['category']
    ordering_fields = ['created_at', 'title', 'popular', 'rating']
    from .filters import CatalogOrderingFilter
    from django_filters.rest_framework import DjangoFilterBackend
    from rest_framework.filters import SearchFilter
    filter_backends = [DjangoFilterBackend, SearchFilter, CatalogOrderingFilter]

    def get_queryset(self):
        qs = catalog_queryset(self.request)

        # Custom filter: rating
        min_rating = self.request.query_params.get('min_rating')
        if min_rating:
            try:
                from django.db.models import Avg
                qs = qs.annotate(avg_rating=Avg('reviews__rating')).filter(avg_rating__gte=float(min_rating))
            except (ValueError, TypeError):
                pass

        # Custom ordering
        ordering = self.request.query_params.get('ordering')
        if ordering == 'popular':
            from django.db.models import Count
            qs = qs.annotate(students=Count('enrollments')).order_by('-students')
        elif ordering == 'rating':
            from django.db.models import Avg
            qs = qs.annotate(avg=Avg('reviews__rating')).order_by('-avg')

        return qs


class CourseDetailView(generics.RetrieveAPIView):
    serializer_class = CourseDetailSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'slug'

    def get_queryset(self):
        return catalog_queryset(self.request).prefetch_related('lessons')


class LessonDetailView(generics.RetrieveAPIView):
    serializer_class = LessonDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Lesson.objects.filter(is_published=True, course__is_published=True).select_related('course').prefetch_related('attachments')

    def get_object(self):
        obj = super().get_object()
        if not obj.is_free_preview and not self.request.user.has_active_subscription:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Obuna kerak")
        return obj


class EnrollmentView(generics.ListCreateAPIView):
    serializer_class = EnrollmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.request.user.enrollments.select_related('course')

    def create(self, request, *args, **kwargs):
        course_id = request.data.get('course')
        from django.shortcuts import get_object_or_404
        from .serializers import EnrollmentSerializer
        incoming = EnrollmentSerializer(data=request.data)
        incoming.is_valid(raise_exception=True)
        course = get_object_or_404(Course, pk=incoming.validated_data['course'].pk, is_published=True)
        enrollment, created = Enrollment.objects.get_or_create(user=request.user, course=course)
        return Response(
            EnrollmentSerializer(enrollment).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


def _generate_signed_token(lesson_id, user_id):
    expiry = int(time.time()) + settings.SIGNED_URL_EXPIRY
    message = f"{lesson_id}:{user_id}:{expiry}"
    signature = hmac.new(
        settings.SECRET_KEY.encode(),
        message.encode(),
        hashlib.sha256,
    ).hexdigest()
    return f"{expiry}:{signature}"


def _verify_signed_token(lesson_id, user_id, token):
    try:
        expiry, signature = token.split(':', 1)
        expiry = int(expiry)
    except (ValueError, AttributeError):
        return False
    if time.time() > expiry:
        return False
    message = f"{lesson_id}:{user_id}:{expiry}"
    expected = hmac.new(
        settings.SECRET_KEY.encode(),
        message.encode(),
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_video_url(request, lesson_id):
    user = request.user
    try:
        lesson = Lesson.objects.get(id=lesson_id, is_published=True, course__is_published=True)
    except Lesson.DoesNotExist:
        return Response({'detail': 'Topilmadi'}, status=status.HTTP_404_NOT_FOUND)

    if not lesson.is_free_preview and not user.has_active_subscription:
        return Response({'detail': 'Obuna kerak'}, status=status.HTTP_403_FORBIDDEN)

    if not hasattr(lesson, 'video') or lesson.video.status != 'ready':
        return Response({'detail': 'Video hali tayyor emas'}, status=status.HTTP_404_NOT_FOUND)

    from videos.streaming import create_stream_token
    token = create_stream_token(lesson_id, user.pk, request.auth['device'])
    video_url = f'/api/videos/stream/{lesson_id}/master.m3u8?token={token}'

    progress = user.progresses.filter(lesson=lesson).first()

    response = Response({
        'url': video_url,
        'resume_at': progress.watched_seconds if progress else 0,
        'watermark_id': user.display_id,
        'token': token,
        'expires_in': settings.SIGNED_URL_EXPIRY,
    })
    response.set_signed_cookie('stream_device', str(request.auth['device']), salt='stream-device',
        max_age=604800, httponly=True, secure=not settings.DEBUG, samesite='Lax', path='/api/videos/')
    return response


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def verify_video_token(request):
    token = request.GET.get('token')
    lesson_id = request.GET.get('lesson_id')
    user_id = request.GET.get('uid')

    if not all([token, lesson_id, user_id]):
        return Response({'valid': False}, status=status.HTTP_400_BAD_REQUEST)

    valid = _verify_signed_token(lesson_id, user_id, token)
    return Response({'valid': valid})
