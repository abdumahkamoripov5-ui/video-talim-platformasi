from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import UserDevice, VideoProgress

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('email', 'full_name', 'phone', 'password', 'password2')

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError({'password': 'Parollar mos kelmadi'})
        from django.contrib.auth.password_validation import validate_password
        from django.core.exceptions import ValidationError
        try:
            validate_password(data['password'])
        except ValidationError as exc:
            raise serializers.ValidationError({'password': exc.messages})
        return data

    def create(self, validated_data):
        validated_data.pop('password2')
        return User.objects.create_user(**validated_data)


class UserProfileSerializer(serializers.ModelSerializer):
    has_active_subscription = serializers.BooleanField(read_only=True)
    display_id = serializers.CharField(read_only=True)
    active_devices_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id', 'email', 'full_name', 'phone', 'avatar',
            'subscription_start', 'subscription_end', 'has_active_subscription',
            'display_id', 'active_devices_count', 'created_at',
        )
        read_only_fields = ('id', 'email', 'subscription_start', 'subscription_end', 'created_at')

    def get_active_devices_count(self, obj):
        return obj.devices.count()


class UserDeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserDevice
        fields = ('id', 'device_id', 'device_name', 'ip_address', 'last_seen', 'created_at')
        read_only_fields = ('ip_address', 'last_seen', 'created_at')


class VideoProgressSerializer(serializers.ModelSerializer):
    lesson_title = serializers.CharField(source='lesson.title', read_only=True)
    course_id = serializers.IntegerField(source='lesson.course_id', read_only=True)

    class Meta:
        model = VideoProgress
        fields = ('id', 'lesson', 'lesson_title', 'course_id', 'watched_seconds', 'is_completed', 'updated_at')
        read_only_fields = ('updated_at',)
