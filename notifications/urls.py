from django.urls import path
from . import views

urlpatterns = [
    path('', views.NotificationListView.as_view()),
    path('announcements/', views.AnnouncementListView.as_view()),
    path('unread-count/', views.unread_count),
    path('<int:notification_id>/read/', views.mark_read),
    path('mark-all-read/', views.mark_all_read),
    path('telegram/webhook/', views.telegram_webhook),
]
