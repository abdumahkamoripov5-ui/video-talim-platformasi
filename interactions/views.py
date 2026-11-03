from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from .models import Wishlist, Review, LessonComment, Question, Answer, Certificate
from .serializers import (
    WishlistSerializer, ReviewSerializer, LessonCommentSerializer,
    QuestionSerializer, AnswerSerializer, CertificateSerializer,
)


# ===== Wishlist =====
class WishlistView(generics.ListCreateAPIView):
    serializer_class = WishlistSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.request.user.wishlist.select_related('course')

    def create(self, request, *args, **kwargs):
        incoming = WishlistSerializer(data=request.data)
        incoming.is_valid(raise_exception=True)
        course_id = incoming.validated_data['course'].pk
        if not incoming.validated_data['course'].is_published:
            return Response({'detail': 'Kurs topilmadi'}, status=404)
        wishlist, created = Wishlist.objects.get_or_create(
            user=request.user, course_id=course_id
        )
        return Response(
            WishlistSerializer(wishlist).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )


@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated])
def remove_from_wishlist(request, course_id):
    deleted, _ = Wishlist.objects.filter(user=request.user, course_id=course_id).delete()
    if deleted:
        return Response({'detail': "O'chirildi"})
    return Response({'detail': 'Topilmadi'}, status=status.HTTP_404_NOT_FOUND)


# ===== Reviews =====
class CourseReviewsView(generics.ListCreateAPIView):
    serializer_class = ReviewSerializer

    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        course_id = self.kwargs.get('course_id')
        return Review.objects.filter(course_id=course_id, is_published=True).select_related('user')

    def create(self, request, *args, **kwargs):
        course_id = self.kwargs.get('course_id')
        incoming = ReviewSerializer(data={**request.data, 'course': course_id})
        incoming.is_valid(raise_exception=True)
        rating = incoming.validated_data['rating']
        comment = incoming.validated_data.get('comment', '')

        review, _ = Review.objects.update_or_create(
            user=request.user,
            course_id=course_id,
            defaults={'rating': rating, 'comment': comment},
        )
        return Response(ReviewSerializer(review).data, status=status.HTTP_201_CREATED)


# ===== Lesson Comments =====
class LessonCommentsView(generics.ListCreateAPIView):
    serializer_class = LessonCommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        lesson_id = self.kwargs.get('lesson_id')
        return LessonComment.objects.filter(
            lesson_id=lesson_id, parent__isnull=True, is_published=True
        ).select_related('user')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user, lesson_id=self.kwargs.get('lesson_id'))


@api_view(['GET'])
def comment_replies(request, comment_id):
    replies = LessonComment.objects.filter(
        parent_id=comment_id, is_published=True
    ).select_related('user')
    return Response(LessonCommentSerializer(replies, many=True).data)


# ===== Questions & Answers =====
class QuestionListView(generics.ListCreateAPIView):
    serializer_class = QuestionSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        qs = Question.objects.select_related('user').prefetch_related('answers__author')
        lesson_id = self.request.query_params.get('lesson')
        course_id = self.request.query_params.get('course')
        my = self.request.query_params.get('my')

        if lesson_id:
            qs = qs.filter(lesson_id=lesson_id)
        if course_id:
            qs = qs.filter(course_id=course_id)
        if my == '1' and self.request.user.is_authenticated:
            qs = qs.filter(user=self.request.user)
        return qs

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class QuestionDetailView(generics.RetrieveDestroyAPIView):
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_destroy(self, instance):
        from rest_framework.exceptions import PermissionDenied
        if instance.user_id != self.request.user.pk and not self.request.user.is_staff:
            raise PermissionDenied('Faqat o‘z savolingizni o‘chirishingiz mumkin.')
        instance.delete()


class AnswerCreateView(generics.CreateAPIView):
    serializer_class = AnswerSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


# ===== Certificates =====
class MyCertificatesView(generics.ListAPIView):
    serializer_class = CertificateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.request.user.certificates.select_related('course')


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def issue_certificate(request, course_id):
    from courses.models import Course
    try:
        course = Course.objects.get(id=course_id)
    except Course.DoesNotExist:
        return Response({'detail': 'Kurs topilmadi'}, status=status.HTTP_404_NOT_FOUND)

    enrollment = request.user.enrollments.filter(course=course).first()
    if not enrollment:
        return Response({'detail': 'Kursga yozilmagansiz'}, status=status.HTTP_403_FORBIDDEN)

    if enrollment.get_progress() < 100:
        return Response(
            {'detail': "Sertifikat olish uchun kursni 100% tugatish kerak"},
            status=status.HTTP_400_BAD_REQUEST
        )

    cert, created = Certificate.objects.get_or_create(user=request.user, course=course)
    return Response(
        CertificateSerializer(cert).data,
        status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
    )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def download_certificate(request, certificate_id):
    """Sertifikatni PDF holida yuklab beradi"""
    from django.http import HttpResponse
    from io import BytesIO
    from reportlab.lib.pagesizes import landscape, A4
    from reportlab.pdfgen import canvas
    from reportlab.lib.colors import HexColor
    from reportlab.lib.units import cm

    try:
        cert = Certificate.objects.select_related('user', 'course').get(
            id=certificate_id, user=request.user
        )
    except Certificate.DoesNotExist:
        return Response({'detail': 'Topilmadi'}, status=status.HTTP_404_NOT_FOUND)

    buffer = BytesIO()
    width, height = landscape(A4)
    c = canvas.Canvas(buffer, pagesize=landscape(A4))

    # Border
    c.setStrokeColor(HexColor('#6366F1'))
    c.setLineWidth(8)
    c.rect(1*cm, 1*cm, width - 2*cm, height - 2*cm)
    c.setStrokeColor(HexColor('#EC4899'))
    c.setLineWidth(2)
    c.rect(1.5*cm, 1.5*cm, width - 3*cm, height - 3*cm)

    # Title
    c.setFillColor(HexColor('#6366F1'))
    c.setFont("Helvetica-Bold", 48)
    c.drawCentredString(width/2, height - 4*cm, "SERTIFIKAT")

    c.setFillColor(HexColor('#64748B'))
    c.setFont("Helvetica", 16)
    c.drawCentredString(width/2, height - 5*cm, "muvaffaqiyatli yakunlash uchun")

    # User name
    c.setFillColor(HexColor('#0F172A'))
    c.setFont("Helvetica-Bold", 32)
    c.drawCentredString(width/2, height/2 + 1*cm, cert.user.full_name)

    # Course name
    c.setFillColor(HexColor('#64748B'))
    c.setFont("Helvetica", 14)
    c.drawCentredString(width/2, height/2 - 0.5*cm, "kursini muvaffaqiyatli tugatdi:")

    c.setFillColor(HexColor('#6366F1'))
    c.setFont("Helvetica-Bold", 22)
    c.drawCentredString(width/2, height/2 - 2*cm, cert.course.title)

    # Footer
    c.setFillColor(HexColor('#94A3B8'))
    c.setFont("Helvetica", 11)
    c.drawString(3*cm, 2.5*cm, f"Sertifikat raqami: {cert.certificate_number}")
    c.drawString(3*cm, 2*cm, f"Berilgan sana: {cert.issued_at.strftime('%d.%m.%Y')}")

    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(HexColor('#6366F1'))
    c.drawRightString(width - 3*cm, 2.5*cm, "EduPlatform")
    c.setFont("Helvetica", 10)
    c.setFillColor(HexColor('#94A3B8'))
    c.drawRightString(width - 3*cm, 2*cm, "eduplatform.uz")

    c.showPage()
    c.save()

    pdf = buffer.getvalue()
    buffer.close()

    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="certificate-{cert.certificate_number}.pdf"'
    return response
