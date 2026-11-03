from django.urls import path
from . import views

urlpatterns = [
    path('', views.CourseListView.as_view()),
    path('categories/', views.CategoryListView.as_view()),
    path('enrollments/', views.EnrollmentView.as_view()),
    path('verify-token/', views.verify_video_token),
    path('lessons/<int:pk>/', views.LessonDetailView.as_view()),
    path('lessons/<int:lesson_id>/video-url/', views.get_video_url),
    path('<slug:slug>/', views.CourseDetailView.as_view()),
]
