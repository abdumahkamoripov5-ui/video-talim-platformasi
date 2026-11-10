from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from .models import Announcement, Notification, TelegramSubscriber
from .serializers import AnnouncementSerializer, NotificationSerializer, TelegramSubscriberSerializer


class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.request.user.notifications.all()


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def unread_count(request):
    count = request.user.notifications.filter(is_read=False).count()
    return Response({'count': count})


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def mark_read(request, notification_id):
    Notification.objects.filter(id=notification_id, user=request.user).update(is_read=True)
    return Response({'detail': "O'qilgan deb belgilandi"})


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def mark_all_read(request):
    request.user.notifications.filter(is_read=False).update(is_read=True)
    return Response({'detail': "Hammasi o'qilgan"})


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def link_telegram(request):
    chat_id = request.data.get('chat_id')
    username = request.data.get('username', '')

    if not chat_id:
        return Response({'detail': 'chat_id majburiy'}, status=status.HTTP_400_BAD_REQUEST)

    sub, _ = TelegramSubscriber.objects.update_or_create(
        user=request.user,
        defaults={'chat_id': chat_id, 'username': username, 'is_active': True},
    )
    return Response(TelegramSubscriberSerializer(sub).data)


class AnnouncementListView(generics.ListAPIView):
    """Faol e'lonlar (ochiq, login talab qilinmaydi)."""
    serializer_class = AnnouncementSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None

    def get_queryset(self):
        return Announcement.objects.filter(is_published=True)[:5]
