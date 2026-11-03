from django.urls import path
from . import views

urlpatterns = [
    path('tariffs/', views.TariffListView.as_view()),
    path('history/', views.PaymentHistoryView.as_view()),
    path('create/', views.create_payment),
    path('webhook/uzum/<str:action>/', views.uzum_webhook),
    path('webhook/payme/', views.payme_webhook),
    path('webhook/click/', views.click_webhook),
]
