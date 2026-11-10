from django.conf import settings
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


class AnnouncementListView(generics.ListAPIView):
    """Faol e'lonlar (ochiq, login talab qilinmaydi)."""
    serializer_class = AnnouncementSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None

    def get_queryset(self):
        return Announcement.objects.filter(is_published=True)[:5]


WELCOME_TEXT = (
    "Video Ta'lim - onlayn ta'lim platformasi.\n\n"
    "Bu yerda siz video darslar, ovozli darslar va o'quv materiallari bilan "
    "istalgan vaqtda, istalgan qurilmada o'rganasiz. Obuna orqali kurslarga to'liq kirish olasiz.\n\n"
    "Boshlash uchun ro'yxatdan o'ting yoki hisobingizga kiring."
)


def _send_telegram(method, payload):
    import requests
    token = settings.TELEGRAM_BOT_TOKEN
    if not token:
        return False
    try:
        return requests.post(f'https://api.telegram.org/bot{token}/{method}', json=payload, timeout=10).ok
    except Exception:
        return False


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def telegram_webhook(request):
    """Telegram botiga kelgan xabarlar. Telegram webhook secret token bilan himoyalangan."""
    secret = settings.TELEGRAM_WEBHOOK_SECRET
    if not secret or request.headers.get('X-Telegram-Bot-Api-Secret-Token') != secret:
        return Response({'detail': 'Ruxsat yo' + chr(39) + 'q'}, status=status.HTTP_403_FORBIDDEN)
    message = (request.data or {}).get('message') or {}
    text = (message.get('text') or '').strip()
    chat = message.get('chat') or {}
    if text.split(' ')[0].split('@')[0] == '/start' and chat.get('id') and chat.get('type') == 'private':
        base = settings.TELEGRAM_WEBAPP_URL.rstrip('/')
        _send_telegram('sendMessage', {
            'chat_id': chat['id'],
            'text': WELCOME_TEXT,
            'reply_markup': {'inline_keyboard': [
                [{'text': "Ro'yxatdan o'tish", 'web_app': {'url': f'{base}/register'}}],
                [{'text': 'Kirish', 'web_app': {'url': f'{base}/login'}}],
                [{'text': 'Ilovani ochish', 'web_app': {'url': base + '/'}}],
            ]},
        })
    return Response({'ok': True})
