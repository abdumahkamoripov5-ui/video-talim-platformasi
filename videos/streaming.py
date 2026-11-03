from pathlib import Path
from urllib.parse import urlencode
from django.conf import settings
from django.core import signing
from django.http import FileResponse, HttpResponse, Http404
from rest_framework.decorators import api_view, permission_classes, authentication_classes, throttle_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from courses.models import LessonAttachment
from users.models import UserDevice
from videos.models import Video


def create_stream_token(lesson, user, device):
    return signing.dumps({'lesson': lesson, 'user': str(user), 'device': device}, salt='video-stream', compress=True)


@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
@throttle_classes([])
def stream(request, lesson_id, asset):
    token = request.query_params.get('token', '')
    try:
        data = signing.loads(token, salt='video-stream', max_age=settings.SIGNED_URL_EXPIRY)
        cookie = request.get_signed_cookie('stream_device', salt='stream-device', default='')
        # HLS.js uses the signed HttpOnly cookie; native apps can use their JWT.
        if str(data['device']) != cookie:
            from users.authentication import DeviceJWTAuthentication
            auth = DeviceJWTAuthentication().authenticate(request)
            if not auth or str(auth[0].pk) != data['user'] or auth[1].get('device') != data['device']:
                return Response({'detail': 'Qurilma tasdiqlanmadi'}, status=403)
        device = UserDevice.objects.select_related('user').get(pk=data['device'], user_id=data['user'], user__is_active=True)
        video = Video.objects.select_related('lesson__course').get(lesson_id=lesson_id, status='ready', lesson__is_published=True, lesson__course__is_published=True)
        if data['lesson'] != lesson_id or (not video.lesson.is_free_preview and not device.user.has_active_subscription):
            return Response({'detail': 'Obuna kerak'}, status=403)
    except (signing.BadSignature, KeyError, ValueError, UserDevice.DoesNotExist, Video.DoesNotExist):
        return Response({'detail': 'Video havolasi eskirgan yoki yaroqsiz'}, status=403)
    from django.utils import timezone
    UserDevice.objects.filter(pk=device.pk).update(last_seen=timezone.now())
    root = (settings.MEDIA_ROOT / video.hls_path).resolve()
    target = (root / asset).resolve()
    if not target.is_relative_to(root) or target.suffix not in {'.m3u8', '.ts'} or not target.is_file():
        raise Http404
    if target.suffix == '.m3u8':
        lines = []
        for line in target.read_text().splitlines():
            if line and not line.startswith('#'):
                line += '?' + urlencode({'token': token})
            lines.append(line)
        response = HttpResponse('\n'.join(lines) + '\n', content_type='application/vnd.apple.mpegurl')
    else:
        response = FileResponse(target.open('rb'), content_type='video/mp2t')
    response['Cache-Control'] = 'private, no-store'
    response['X-Content-Type-Options'] = 'nosniff'
    return response


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def attachment(request, attachment_id):
    try:
        obj = LessonAttachment.objects.select_related('lesson__course').get(pk=attachment_id, lesson__is_published=True, lesson__course__is_published=True)
    except LessonAttachment.DoesNotExist:
        raise Http404
    if not obj.lesson.is_free_preview and not request.user.has_active_subscription:
        return Response({'detail': 'Obuna kerak'}, status=403)
    if not obj.file or not Path(obj.file.path).is_file():
        raise Http404
    return FileResponse(obj.file.open('rb'), as_attachment=True, filename=Path(obj.file.name).name)


def public_media(request, path):
    # Original videos, HLS segments and lesson files are never public.
    from django.views.static import serve
    if Path(path).suffix.lower() not in {'.png', '.jpg', '.jpeg', '.webp', '.gif', '.avif'}:
        raise Http404
    if path.split('/')[0] not in {'avatars', 'courses', 'lessons'} or path.startswith('lessons/attachments/'):
        raise Http404
    return serve(request, path, document_root=settings.MEDIA_ROOT)
