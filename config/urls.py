from videos import direct_upload
from config.health import health
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from videos.streaming import public_media
from django.urls import re_path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('api/health/', health, name='health'),
    path('admin/media-upload/', admin.site.admin_view(direct_upload.upload_page), name='media-upload'),
    path('admin/media-upload/start/', admin.site.admin_view(direct_upload.initiate)),
    path('admin/media-upload/configure/', admin.site.admin_view(direct_upload.configure_storage)),
    path('admin/media-upload/<uuid:upload_id>/complete/', admin.site.admin_view(direct_upload.complete)),
    path('admin/', admin.site.urls),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/users/', include('users.urls')),
    path('api/courses/', include('courses.urls')),
    path('api/payments/', include('payments.urls')),
    path('api/videos/', include('videos.urls')),
    path('api/interactions/', include('interactions.urls')),
    path('api/quizzes/', include('quizzes.urls')),
    path('api/notifications/', include('notifications.urls')),
]
if settings.DEBUG:
    urlpatterns += [re_path(r'^media/(?P<path>.*)$', public_media)]

if settings.IS_VERCEL:
    from config.frontend import frontend, public_asset
    urlpatterns += [
        re_path(r'^(?P<filename>manifest\.json|sw\.js|icon-192\.svg|icon-512\.svg)$', public_asset),
        re_path(r'^(?P<path>.*)$', frontend),
    ]
