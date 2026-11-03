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
