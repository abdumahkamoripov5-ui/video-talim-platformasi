import os
import subprocess
from django.conf import settings
from rest_framework import permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from rest_framework.views import APIView
from .models import Video
from courses.models import Lesson


class VideoUploadView(APIView):
    parser_classes = [MultiPartParser]
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, lesson_id):
        if settings.OBJECT_STORAGE_ENABLED or settings.IS_VERCEL:
            return Response({'detail': 'Video uchun /admin/media-upload/ sahifasidan foydalaning'}, status=503)
        try:
            lesson = Lesson.objects.get(id=lesson_id)
        except Lesson.DoesNotExist:
            return Response({'detail': 'Dars topilmadi'}, status=status.HTTP_404_NOT_FOUND)

        file = request.FILES.get('video')
        if not file:
            return Response({'detail': 'Video fayl majburiy'}, status=400)
        if file.size > settings.MAX_VIDEO_UPLOAD_BYTES:
            return Response({'detail': 'Video hajmi ruxsat etilgan chegaradan katta'}, status=400)
        if os.path.splitext(file.name)[1].lower() not in {'.mp4', '.mov', '.mkv', '.webm', '.avi'}:
            return Response({'detail': 'Video formati qo‘llab-quvvatlanmaydi'}, status=400)
        video, _ = Video.objects.get_or_create(lesson=lesson)
        if video.status == 'processing':
            return Response({'detail': 'Avvalgi video qayta ishlanmoqda'}, status=409)
        video.original_file.save(file.name, file, save=False)
        video.status = 'processing'
        video.error_message = ''
        video.save()
        from .tasks import convert_video
        try:
            convert_video.delay(video.pk)
        except Exception:
            video.status = 'failed'
            video.error_message = 'Video navbatiga ulanish amalga oshmadi. Worker va Redisni tekshiring.'
            video.save(update_fields=['status', 'error_message'])
            return Response({'detail': 'Video qayta ishlash xizmati vaqtincha ishlamayapti'}, status=503)
        video.refresh_from_db()
        return Response({'id': video.pk, 'status': video.status}, status=202)



def _convert_to_hls(video, input_path, lesson_id):
    output_dir = os.path.join(settings.MEDIA_ROOT, 'videos', 'hls', str(lesson_id))
    os.makedirs(output_dir, exist_ok=True)

    qualities = [
        ('360p', '640x360', '800k', '96k'),
        ('720p', '1280x720', '2800k', '128k'),
        ('1080p', '1920x1080', '5000k', '192k'),
    ]

    variant_playlists = []
    video.has_360p = video.has_720p = video.has_1080p = False

    for name, size, vbitrate, abitrate in qualities:
        quality_dir = os.path.join(output_dir, name)
        os.makedirs(quality_dir, exist_ok=True)

        cmd = [
            'ffmpeg', '-i', input_path,
            '-vf', f"scale={size.replace('x', ':')}:force_original_aspect_ratio=decrease,pad={size.replace('x', ':')}:(ow-iw)/2:(oh-ih)/2,setsar=1",
            '-pix_fmt', 'yuv420p', '-force_key_frames', 'expr:gte(t,n_forced*6)',
            '-c:v', 'libx264', '-b:v', vbitrate, '-preset', 'fast',
            '-c:a', 'aac', '-b:a', abitrate,
            '-hls_time', '6', '-hls_flags', 'independent_segments',
            '-hls_playlist_type', 'vod',
            '-hls_segment_filename', os.path.join(quality_dir, 'seg_%03d.ts'),
            os.path.join(quality_dir, 'index.m3u8'),
            '-y',
        ]
        try:
            subprocess.run(cmd, check=True, capture_output=True, timeout=21600)
            bw = int(vbitrate.replace('k', '')) * 1000
            variant_playlists.append(
                f"#EXT-X-STREAM-INF:BANDWIDTH={bw},RESOLUTION={size}\n{name}/index.m3u8"
            )
            setattr(video, f'has_{name}', True)
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            pass

    if variant_playlists:
        master = "#EXTM3U\n" + "\n".join(variant_playlists)
        with open(os.path.join(output_dir, 'master.m3u8'), 'w') as f:
            f.write(master)
        video.error_message = ''
        video.hls_path = f"videos/hls/{lesson_id}"
        video.status = 'ready'
        video.playback_format = 'hls'

        # Duration olish
        try:
            result = subprocess.run(
                ['ffprobe', '-v', 'quiet', '-show_entries', 'format=duration',
                 '-of', 'csv=p=0', input_path],
                capture_output=True, text=True, timeout=30
            )
            video.duration_seconds = int(float(result.stdout.strip()))
            Lesson.objects.filter(pk=lesson_id).update(duration_seconds=video.duration_seconds)
        except Exception:
            pass
    else:
        video.status = 'failed'
        video.error_message = 'FFmpeg topilmadi yoki konvertatsiya muvaffaqiyatsiz'

    video.save()


@api_view(['GET'])
@permission_classes([permissions.IsAdminUser])
def video_status(request, lesson_id):
    try:
        video = Video.objects.get(lesson_id=lesson_id)
        return Response({
            'status': video.status,
            'has_360p': video.has_360p,
            'has_720p': video.has_720p,
            'has_1080p': video.has_1080p,
            'duration_seconds': video.duration_seconds,
            'error': video.error_message,
        })
    except Video.DoesNotExist:
        return Response({'detail': 'Video topilmadi'}, status=status.HTTP_404_NOT_FOUND)
