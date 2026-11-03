from django.contrib import admin
from django.db import transaction
from .models import Video
from .tasks import convert_video

@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ('lesson', 'status', 'duration_seconds', 'has_360p', 'has_720p', 'has_1080p', 'updated_at')
    list_filter = ('status',)
    search_fields = ('lesson__title', 'lesson__course__title')
    readonly_fields = ('status', 'hls_path', 'duration_seconds', 'has_360p', 'has_720p', 'has_1080p', 'error_message', 'created_at', 'updated_at')
    actions = ['retry_conversion']

    def save_model(self, request, obj, form, change):
        upload = 'original_file' in form.changed_data and obj.original_file
        if upload:
            obj.status = 'processing'
        super().save_model(request, obj, form, change)
        if upload:
            transaction.on_commit(lambda: convert_video.delay(obj.pk))

    @admin.action(description='Videoni qayta konvertatsiya qilish')
    def retry_conversion(self, request, queryset):
        for video in queryset.exclude(status='processing'):
            if video.original_file:
                video.status = 'processing'
                video.save(update_fields=['status'])
                convert_video.delay(video.pk)
