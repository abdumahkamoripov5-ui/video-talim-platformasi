from django.conf import settings
from django.db import transaction
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User, UserDevice


def attach_device(user, data, request):
    device_id = data.get('device_id', '')
    if not isinstance(device_id, str) or not 8 <= len(device_id) <= 255:
        from rest_framework.exceptions import ValidationError
        raise ValidationError({'device_id': 'Qurilma identifikatori majburiy (8–255 belgi).'})
    with transaction.atomic():
        User.objects.select_for_update().get(pk=user.pk)
        device = user.devices.filter(device_id=device_id).first()
        if not device and user.devices.count() >= settings.MAX_DEVICES:
            raise PermissionDenied(f'Qurilmalar soni oshib ketdi. Maksimum {settings.MAX_DEVICES} ta qurilma ruxsat etiladi.')
        device, _ = UserDevice.objects.update_or_create(user=user, device_id=device_id, defaults={
            'device_name': str(data.get('device_name', 'Veb brauzer'))[:255],
            'user_agent': request.META.get('HTTP_USER_AGENT', '')[:1000],
            'ip_address': request.META.get('REMOTE_ADDR'),
        })
        return device


class DeviceTokenSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        device = attach_device(self.user, self.initial_data, self.context['request'])
        refresh = RefreshToken.for_user(self.user)
        refresh['device'] = device.pk
        data.update(refresh=str(refresh), access=str(refresh.access_token))
        return data


class DeviceRefreshSerializer(TokenRefreshSerializer):
    def validate(self, attrs):
        token = RefreshToken(attrs['refresh'])
        if not UserDevice.objects.filter(pk=token.get('device'), user_id=token.get('user_id'), user__is_active=True).exists():
            raise AuthenticationFailed('Qurilma sessiyasi tugagan. Qayta kiring.')
        return super().validate(attrs)


class DeviceJWTAuthentication(JWTAuthentication):
    def get_user(self, validated_token):
        user = super().get_user(validated_token)
        device = UserDevice.objects.filter(pk=validated_token.get('device'), user=user).first()
        if device is None:
            raise AuthenticationFailed('Qurilma sessiyasi tugagan. Qayta kiring.')
        return user
