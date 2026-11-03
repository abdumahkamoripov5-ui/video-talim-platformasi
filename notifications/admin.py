from django.contrib import admin
from .models import Notification, TelegramSubscriber


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'type', 'title', 'is_read', 'created_at')
    list_filter = ('type', 'is_read')
    search_fields = ('user__email', 'title', 'message')


@admin.register(TelegramSubscriber)
class TelegramSubscriberAdmin(admin.ModelAdmin):
    list_display = ('user', 'username', 'chat_id', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('user__email', 'username', 'chat_id')
