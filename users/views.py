from django.conf import settings
from django.db import transaction
from .authentication import attach_device
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from .models import UserDevice, VideoProgress
from .serializers import (
    RegisterSerializer, UserProfileSerializer,
    UserDeviceSerializer, VideoProgressSerializer,
)

User = get_user_model()


def get_client_ip(request):
    x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded:
        return x_forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


class RegisterView(generics.CreateAPIView):
    throttle_scope = 'auth'
    from rest_framework.throttling import ScopedRateThrottle
    throttle_classes = [ScopedRateThrottle]
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            user = serializer.save()
            device = attach_device(user, request.data, request)
        refresh = RefreshToken.for_user(user)
        refresh['device'] = device.pk
        return Response({
            'user': UserProfileSerializer(user).data,
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }, status=status.HTTP_201_CREATED)


class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class DeviceListView(generics.ListAPIView):
    serializer_class = UserDeviceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.request.user.devices.all()


@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated])
def remove_device(request, device_id):
    deleted, _ = request.user.devices.filter(id=device_id).delete()
    if deleted:
        return Response({'detail': "Qurilma o'chirildi"})
    return Response({'detail': 'Topilmadi'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def register_device(request):
    device_id = request.data.get('device_id')
    device_name = request.data.get('device_name', '')

    if not device_id:
        return Response({'detail': 'device_id majburiy'}, status=status.HTTP_400_BAD_REQUEST)

    device = attach_device(request.user, request.data, request)
    return Response(UserDeviceSerializer(device).data)


class VideoProgressView(generics.ListCreateAPIView):
    serializer_class = VideoProgressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.request.user.progresses.select_related('lesson__course')

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        lesson = serializer.validated_data['lesson']
        if not lesson.is_published or not lesson.course.is_published:
            return Response({'detail': 'Dars topilmadi'}, status=404)
        if not lesson.is_free_preview and not request.user.has_active_subscription:
            return Response({'detail': 'Obuna kerak'}, status=403)
        watched = serializer.validated_data.get('watched_seconds', 0)
        duration = lesson.duration_seconds or getattr(getattr(lesson, 'video', None), 'duration_seconds', 0)
        if duration:
            watched = min(watched, duration)
        completed = bool(duration and watched >= duration * .9)
        with transaction.atomic():
            progress, _ = VideoProgress.objects.select_for_update().get_or_create(user=request.user, lesson=lesson)
            progress.watched_seconds = watched
            progress.is_completed = progress.is_completed or completed
            progress.save()
            from courses.models import Enrollment
            Enrollment.objects.get_or_create(user=request.user, course=lesson.course)
        return Response(self.get_serializer(progress).data)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def logout(request):
    request.user.devices.filter(pk=request.auth.get('device')).delete()
    response = Response({'detail': 'Sessiya yopildi'})
    response.delete_cookie('stream_device', path='/api/videos/')
    return response


from rest_framework.throttling import ScopedRateThrottle
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .authentication import DeviceTokenSerializer, DeviceRefreshSerializer

class LoginView(TokenObtainPairView):
    serializer_class = DeviceTokenSerializer
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'auth'

class RefreshView(TokenRefreshView):
    serializer_class = DeviceRefreshSerializer
