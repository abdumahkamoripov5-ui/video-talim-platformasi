from config.health import health
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from videos.streaming import public_media
from users.admin_dashboard import dashboard_view
from django.urls import re_path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('api/health/', health, name='health'),
    path('admin/dashboard/', dashboard_view, name='dashboard'),
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
