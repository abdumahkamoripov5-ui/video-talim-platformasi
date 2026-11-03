from rest_framework import serializers
from .models import Notification, TelegramSubscriber


class NotificationSerializer(serializers.ModelSerializer):
    type_display = serializers.CharField(source='get_type_display', read_only=True)

    class Meta:
        model = Notification
        fields = ('id', 'type', 'type_display', 'title', 'message', 'link',
                  'is_read', 'created_at')
        read_only_fields = ('created_at',)


class TelegramSubscriberSerializer(serializers.ModelSerializer):
    class Meta:
        model = TelegramSubscriber
        fields = ('id', 'chat_id', 'username', 'is_active', 'created_at')
        read_only_fields = ('created_at',)
