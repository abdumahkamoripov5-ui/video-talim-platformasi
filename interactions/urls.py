from django.urls import path
from . import views

urlpatterns = [
    # Wishlist
    path('wishlist/', views.WishlistView.as_view()),
    path('wishlist/<int:course_id>/remove/', views.remove_from_wishlist),

    # Reviews
    path('courses/<int:course_id>/reviews/', views.CourseReviewsView.as_view()),

    # Comments
    path('lessons/<int:lesson_id>/comments/', views.LessonCommentsView.as_view()),
    path('comments/<int:comment_id>/replies/', views.comment_replies),

    # Q&A
    path('questions/', views.QuestionListView.as_view()),
    path('questions/<int:pk>/', views.QuestionDetailView.as_view()),
    path('answers/', views.AnswerCreateView.as_view()),

    # Certificates
    path('certificates/', views.MyCertificatesView.as_view()),
    path('certificates/issue/<int:course_id>/', views.issue_certificate),
    path('certificates/<int:certificate_id>/download/', views.download_certificate),
]
