from django.conf import settings
from django.contrib import admin, messages
from django.db import transaction
from .models import Video
from .tasks import convert_video

@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ('lesson', 'playback_format', 'status', 'duration_seconds', 'has_360p', 'has_720p', 'has_1080p', 'updated_at')
    list_filter = ('status',)
    search_fields = ('lesson__title', 'lesson__course__title')
    readonly_fields = ('playback_format', 'status', 'hls_path', 'duration_seconds', 'has_360p', 'has_720p', 'has_1080p', 'error_message', 'created_at', 'updated_at')
    actions = ['retry_conversion']

    def has_add_permission(self, request):
        return not (settings.IS_VERCEL or settings.OBJECT_STORAGE_ENABLED) and super().has_add_permission(request)

    def get_readonly_fields(self, request, obj=None):
        fields = super().get_readonly_fields(request, obj)
        return fields + ('original_file',) if (settings.IS_VERCEL or settings.OBJECT_STORAGE_ENABLED) else fields

    def save_model(self, request, obj, form, change):
        upload = 'original_file' in form.changed_data and obj.original_file
        if upload:
            obj.status = 'processing'
        super().save_model(request, obj, form, change)
        if upload:
            transaction.on_commit(lambda: convert_video.delay(obj.pk))

    @admin.action(description='Videoni qayta konvertatsiya qilish')
    def retry_conversion(self, request, queryset):
        if (settings.IS_VERCEL or settings.OBJECT_STORAGE_ENABLED):
            self.message_user(request, 'Video qayta ishlash xizmati hali ulanmagan.', level=messages.ERROR)
            return
        for video in queryset.exclude(status='processing'):
            if video.original_file:
                video.status = 'processing'
                video.save(update_fields=['status'])
                convert_video.delay(video.pk)
