import io
import json
import logging
from datetime import timedelta
from pathlib import PurePath

from botocore.exceptions import BotoCoreError, ClientError
from django.conf import settings
from django.contrib import admin
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST
from PIL import Image, UnidentifiedImageError
from rest_framework import serializers

from courses.models import Course, Lesson, LessonAttachment
from .models import MediaUpload, Video
from .object_storage import client

logger = logging.getLogger(__name__)

TYPES = {
    'video': {'.mp4': 'video/mp4'},
    'audio': {'.mp3': 'audio/mpeg', '.m4a': 'audio/mp4', '.wav': 'audio/wav'},
    'thumbnail': {'.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png', '.webp': 'image/webp'},
    'attachment': {
        '.pdf': 'application/pdf', '.doc': 'application/msword',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        '.txt': 'text/plain', '.zip': 'application/zip',
    },
}


class UploadRequest(serializers.Serializer):
    kind = serializers.ChoiceField(choices=list(TYPES))
    target_id = serializers.IntegerField(min_value=1)
    filename = serializers.CharField(max_length=200)
    size = serializers.IntegerField(min_value=1)
    title = serializers.CharField(max_length=255, required=False, allow_blank=True, default='')
    duration_seconds = serializers.IntegerField(min_value=0, max_value=86400, default=0)

    def validate(self, data):
        name = data['filename']
        if '/' in name or '\\' in name or any(ord(c) < 32 for c in name):
            raise serializers.ValidationError('Fayl nomi yaroqsiz')
        ext = PurePath(name).suffix.lower()
        if ext not in TYPES[data['kind']]:
            raise serializers.ValidationError('Bu fayl formati qo‘llab-quvvatlanmaydi')
        maximum = {'video': settings.DIRECT_VIDEO_MAX_BYTES, 'audio': settings.DIRECT_VIDEO_MAX_BYTES,
                   'attachment': settings.DIRECT_ATTACHMENT_MAX_BYTES, 'thumbnail': 2 * 1024**2}[data['kind']]
        if data['size'] > maximum:
            raise serializers.ValidationError('Fayl hajmi ruxsat etilgan chegaradan katta')
        data['content_type'] = TYPES[data['kind']][ext]
        return data


def target_for(user, kind, target_id):
    permission = {'thumbnail': 'courses.change_course', 'attachment': 'courses.add_lessonattachment',
                  'video': 'videos.change_video', 'audio': 'videos.change_video'}[kind]
    if not user.has_perm(permission):
        raise PermissionDenied
    return get_object_or_404(Course if kind == 'thumbnail' else Lesson, pk=target_id)


def unavailable():
    return JsonResponse({'detail': 'Object Storage hali ulanmagan. Neon saqlash sozlamalarini kiriting.'}, status=503)


def is_public(storage):
    acl = storage.get_bucket_acl(Bucket=settings.MEDIA_BUCKET)
    return any('AllUsers' in grant.get('Grantee', {}).get('URI', '') for grant in acl.get('Grants', []))


@require_GET
def upload_page(request):
    return render(request, 'admin/media_upload.html', {
        **admin.site.each_context(request), 'title': 'Video va fayl yuklash',
        'enabled': settings.OBJECT_STORAGE_ENABLED,
        'courses': Course.objects.order_by('title'),
        'lessons': Lesson.objects.select_related('course').order_by('course__title', 'order'),
    })


@require_POST
def configure_storage(request):
    if not request.user.is_superuser:
        raise PermissionDenied
    if not settings.OBJECT_STORAGE_ENABLED:
        return unavailable()
    storage = client()
    try:
        storage.head_bucket(Bucket=settings.MEDIA_BUCKET)
        if is_public(storage):
            return JsonResponse({'detail': 'Bucket public. Neon panelida Private qiling.'}, status=400)
        storage.put_bucket_cors(Bucket=settings.MEDIA_BUCKET, CORSConfiguration={'CORSRules': [{
            'AllowedOrigins': [settings.FRONTEND_URL], 'AllowedMethods': ['GET', 'PUT', 'HEAD'],
            'AllowedHeaders': ['*'], 'ExposeHeaders': ['ETag', 'Content-Length', 'Content-Range'],
            'MaxAgeSeconds': 3600,
        }]})
    except (BotoCoreError, ClientError):
        logger.warning('Object storage configuration failed')
        return JsonResponse({'detail': 'Bucket yoki kalitlar yaroqsiz. Read/write ruxsatlarini tekshiring.'}, status=503)
    return JsonResponse({'detail': 'Saqlash xizmati tekshirildi. Brauzer yuklash ruxsati sozlandi.'})


@require_POST
def initiate(request):
    if not settings.OBJECT_STORAGE_ENABLED:
        return unavailable()
    try:
        payload = json.loads(request.body)
    except (ValueError, UnicodeDecodeError):
        return JsonResponse({'detail': 'JSON yaroqsiz'}, status=400)
    serializer = UploadRequest(data=payload)
    if not serializer.is_valid():
        return JsonResponse({'detail': serializer.errors}, status=400)
    data = serializer.validated_data
    target_for(request.user, data['kind'], data['target_id'])
    if MediaUpload.objects.filter(user=request.user, completed=False,
            created_at__gte=timezone.now() - timedelta(hours=1)).count() >= 20:
        return JsonResponse({'detail': 'Tugallanmagan yuklashlar ko‘p. Keyinroq urinib ko‘ring.'}, status=429)
    upload = MediaUpload.objects.create(user=request.user, **data)
    try:
        storage = client()
        if is_public(storage):
            upload.delete()
            return JsonResponse({'detail': 'Bucket public. Neon panelida Private qiling.'}, status=400)
        url = storage.generate_presigned_url('put_object', Params={
            'Bucket': settings.MEDIA_BUCKET, 'Key': upload.staging_key,
            'ContentType': upload.content_type, 'ContentLength': upload.size,
        }, ExpiresIn=3600)
    except (BotoCoreError, ClientError):
        upload.delete()
        logger.warning('Storage upload signing failed')
        return unavailable()
    response = JsonResponse({'id': str(upload.pk), 'url': url, 'content_type': upload.content_type})
    response['Cache-Control'] = 'no-store'
    return response


@require_POST
def complete(request, upload_id):
    if not settings.OBJECT_STORAGE_ENABLED:
        return unavailable()
    with transaction.atomic():
        upload = get_object_or_404(MediaUpload.objects.select_for_update(), pk=upload_id, user=request.user)
        target = target_for(request.user, upload.kind, upload.target_id)
        if upload.completed:
            return JsonResponse({'status': 'ready', 'id': upload.result_id})
        if upload.created_at < timezone.now() - timedelta(hours=2):
            return JsonResponse({'detail': 'Yuklash muddati tugagan. Qayta boshlang.'}, status=400)
        storage = client()
        try:
            head = storage.head_object(Bucket=settings.MEDIA_BUCKET, Key=upload.staging_key)
            if head['ContentLength'] != upload.size or head.get('ContentType') != upload.content_type:
                return JsonResponse({'detail': 'Yuklangan fayl hajmi yoki turi mos kelmadi'}, status=400)
            if upload.kind == 'thumbnail':
                body = storage.get_object(Bucket=settings.MEDIA_BUCKET, Key=upload.staging_key)['Body']
                try:
                    image = Image.open(io.BytesIO(body.read(2 * 1024**2 + 1)))
                    image.verify()
                    if Image.MIME.get(image.format) != upload.content_type:
                        raise ValueError('Image format mismatch')
                finally:
                    body.close()
            # The browser never receives permission to write to final keys.
            # A replayed PUT can only affect the staging object.
            storage.copy_object(Bucket=settings.MEDIA_BUCKET, Key=upload.final_key,
                CopySource={'Bucket': settings.MEDIA_BUCKET, 'Key': upload.staging_key},
                CopySourceIfMatch=head['ETag'], MetadataDirective='REPLACE',
                ContentType=upload.content_type,
                ContentDisposition='attachment' if upload.kind == 'attachment' else 'inline')
        except (ValueError, UnidentifiedImageError, Image.DecompressionBombError, OSError):
            return JsonResponse({'detail': 'Rasm fayli yaroqsiz'}, status=400)
        except (BotoCoreError, ClientError):
            logger.warning('Storage upload finalization failed')
            return JsonResponse({'detail': 'Fayl tekshirilmadi. Saqlash sozlamalari va yuklashni tekshiring.'}, status=503)
        if upload.kind in ('video', 'audio'):
            video, _ = Video.objects.update_or_create(lesson=target, defaults={
                'original_file': upload.final_key, 'playback_format': 'mp4', 'hls_path': '',
                'status': 'ready', 'error_message': '', 'duration_seconds': upload.duration_seconds,
                'has_360p': False, 'has_720p': False, 'has_1080p': False,
            })
            Lesson.objects.filter(pk=target.pk).update(duration_seconds=upload.duration_seconds)
            result_id = video.pk
        elif upload.kind == 'thumbnail':
            target.thumbnail = upload.final_key
            target.save(update_fields=['thumbnail'])
            result_id = target.pk
        else:
            ext = PurePath(upload.filename).suffix.lower()
            result = LessonAttachment.objects.create(lesson=target, file=upload.final_key,
                title=upload.title or upload.filename,
                file_type='pdf' if ext == '.pdf' else 'word' if ext in {'.doc', '.docx'} else 'other')
            result_id = result.pk
        upload.completed = True
        upload.result_id = result_id
        upload.save(update_fields=['completed', 'result_id'])
        transaction.on_commit(lambda: remove_staging(upload.staging_key))
    return JsonResponse({'status': 'ready', 'id': result_id})


def remove_staging(key):
    try:
        client().delete_object(Bucket=settings.MEDIA_BUCKET, Key=key)
    except (BotoCoreError, ClientError):
        logger.warning('Staging object cleanup failed')
