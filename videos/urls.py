from django.urls import path
from . import views
from .streaming import stream, attachment

urlpatterns = [
    path('stream/<int:lesson_id>/<path:asset>', stream),
    path('attachments/<int:attachment_id>/', attachment),
    path('upload/<int:lesson_id>/', views.VideoUploadView.as_view()),
    path('status/<int:lesson_id>/', views.video_status),
]
