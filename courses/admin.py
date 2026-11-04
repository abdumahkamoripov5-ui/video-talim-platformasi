from django.conf import settings
from django.contrib import admin
from django.utils.html import format_html
from videos.models import Video
from .models import Category, Course, Lesson, LessonAttachment, Enrollment


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 0
    fields = ('order', 'title', 'is_published', 'is_free_preview', 'duration_seconds')
    ordering = ('order',)


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'instructor', 'total_lessons', 'is_published', 'created_at')
    list_filter = ('is_published', 'category')
    search_fields = ('title', 'instructor')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [LessonInline]
    readonly_fields = ('created_at', 'updated_at')

    def total_lessons(self, obj):
        return obj.lessons.count()
    total_lessons.short_description = 'Darslar'


class LessonAttachmentInline(admin.TabularInline):
    model = LessonAttachment
    extra = 0


class VideoInline(admin.StackedInline):
    model = Video
    extra = 0
    fields = ('original_file', 'status', 'error_message')
    readonly_fields = ('status', 'error_message')


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'order', 'is_published', 'is_free_preview', 'video_status')
    list_filter = ('is_published', 'is_free_preview', 'course')
    search_fields = ('title', 'course__title')
    inlines = [LessonAttachmentInline, VideoInline]

    def get_inlines(self, request, obj):
        if settings.IS_VERCEL or settings.OBJECT_STORAGE_ENABLED:
            return [LessonAttachmentInline]
        return super().get_inlines(request, obj)

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for deleted in formset.deleted_objects:
            deleted.delete()
        for obj in instances:
            is_video = (isinstance(obj, Video) and obj.original_file
                        and obj.playback_format == 'hls' and not (settings.IS_VERCEL or settings.OBJECT_STORAGE_ENABLED))
            if is_video:
                obj.status = 'processing'
            obj.save()
            if is_video:
                from django.db import transaction
                from videos.tasks import convert_video
                transaction.on_commit(lambda pk=obj.pk: convert_video.delay(pk))
        formset.save_m2m()

    def video_status(self, obj):
        if hasattr(obj, 'video'):
            statuses = {
                'ready': format_html('<span style="color:green">✔ Tayyor</span>'),
                'processing': format_html('<span style="color:orange">⏳ Qayta ishlanmoqda</span>'),
                'failed': format_html('<span style="color:red">✘ Xato</span>'),
                'pending': format_html('<span style="color:gray">⏸ Kutilmoqda</span>'),
            }
            return statuses.get(obj.video.status, '-')
        return format_html('<span style="color:gray">— Yuklanmagan</span>')
    video_status.short_description = 'Video holati'


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'progress_percent', 'enrolled_at')
    search_fields = ('user__email', 'course__title')

    def progress_percent(self, obj):
        return f"{obj.get_progress()}%"
    progress_percent.short_description = 'Progress'
