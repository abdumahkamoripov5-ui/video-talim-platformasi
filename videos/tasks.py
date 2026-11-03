import logging
from celery import shared_task
from .models import Video

logger = logging.getLogger(__name__)

@shared_task(soft_time_limit=22000, time_limit=22100)
def convert_video(video_id):
    from .views import _convert_to_hls
    video = Video.objects.get(pk=video_id)
    try:
        _convert_to_hls(video, video.original_file.path, video.lesson_id)
    except Exception:
        logger.exception('Video conversion failed: %s', video_id)
        Video.objects.filter(pk=video_id).update(status='failed', error_message='Video konvertatsiyasi bajarilmadi. Server jurnalini tekshiring.')
