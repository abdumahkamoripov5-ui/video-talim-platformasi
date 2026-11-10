from django.contrib import admin
from .models import Announcement, Notification, TelegramSubscriber


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    # Admin menyusida yashirilgan (ma'lumot saqlanadi, URL orqali ochiladi)
    def get_model_perms(self, request):
        return {}
    list_display = ('user', 'type', 'title', 'is_read', 'created_at')
    list_filter = ('type', 'is_read')
    search_fields = ('user__email', 'title', 'message')


@admin.register(TelegramSubscriber)
class TelegramSubscriberAdmin(admin.ModelAdmin):
    # Admin menyusida yashirilgan (ma'lumot saqlanadi, URL orqali ochiladi)
    def get_model_perms(self, request):
        return {}
    list_display = ('user', 'username', 'chat_id', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('user__email', 'username', 'chat_id')


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_published', 'published_at')
    list_filter = ('is_published',)
    search_fields = ('title', 'body')
    list_editable = ('is_published',)
