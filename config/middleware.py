from django.http import JsonResponse
from django.conf import settings
from django.contrib.auth import get_user_model


class TemporaryAdminAccessMiddleware:
    """Allow direct admin access until ADMIN_REQUIRE_LOGIN is enabled."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not settings.ADMIN_REQUIRE_LOGIN and request.path_info.startswith('/admin/'):
            User = get_user_model()
            user, _ = User.objects.get_or_create(
                email='temporary-admin@platform.invalid',
                defaults={'full_name': 'Vaqtinchalik admin', 'is_staff': True,
                          'is_superuser': True, 'is_active': True, 'password': '!'},
            )
            if user.is_active and user.is_staff and user.is_superuser:
                request.user = user
        return self.get_response(request)


class VercelUploadGuard:
    """Reject uploads until persistent storage and a video worker are connected."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method in {'POST', 'PUT', 'PATCH'} and request.FILES:
            return JsonResponse({
                'detail': 'Faylni admin paneldagi “Video va fayl yuklash” sahifasidan yuklang: /admin/media-upload/'
            }, status=503)
        return self.get_response(request)
