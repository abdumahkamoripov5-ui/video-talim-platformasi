from django.urls import path
from . import views

urlpatterns = [
    path('lessons/<int:lesson_id>/', views.QuizDetailView.as_view()),
    path('lessons/<int:lesson_id>/submit/', views.submit_quiz),
    path('attempts/', views.MyAttemptsView.as_view()),
]
