import uuid
from django.conf import settings
from django.db import models


class Video(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Kutilmoqda'),
        ('processing', 'Qayta ishlanmoqda'),
        ('ready', 'Tayyor'),
        ('failed', 'Xato'),
    ]

    lesson = models.OneToOneField('courses.Lesson', on_delete=models.CASCADE, related_name='video')
    original_file = models.FileField(upload_to='videos/originals/', null=True, blank=True)
    playback_format = models.CharField(max_length=8, choices=[('hls', 'HLS'), ('mp4', 'MP4')], default='hls')
    hls_path = models.CharField(max_length=500, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    duration_seconds = models.PositiveIntegerField(default=0)

    # HLS quality variants
    has_360p = models.BooleanField(default=False)
    has_720p = models.BooleanField(default=False)
    has_1080p = models.BooleanField(default=False)

    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Video'
        verbose_name_plural = 'Videolar'

    def __str__(self):
        return f"Video: {self.lesson}"

    @property
    def master_playlist_url(self):
        if self.hls_path and self.status == 'ready':
            return f"/media/{self.hls_path}/master.m3u8"
        return None


class MediaUpload(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    kind = models.CharField(max_length=20)
    target_id = models.PositiveBigIntegerField()
    filename = models.CharField(max_length=255)
    content_type = models.CharField(max_length=150)
    size = models.PositiveBigIntegerField()
    title = models.CharField(max_length=255, blank=True)
    duration_seconds = models.PositiveIntegerField(default=0)
    completed = models.BooleanField(default=False)
    result_id = models.PositiveBigIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def staging_key(self):
        return f'uploads/pending/{self.pk}/{self.filename}'

    @property
    def final_key(self):
        return f'uploads/{self.kind}/{self.pk}/{self.filename}'
