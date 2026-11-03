from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views
from rest_framework.throttling import ScopedRateThrottle
from .authentication import DeviceTokenSerializer, DeviceRefreshSerializer

urlpatterns = [
    path('auth/register/', views.RegisterView.as_view()),
    path('auth/login/', views.LoginView.as_view()),
    path('auth/refresh/', views.RefreshView.as_view()),
    path('auth/logout/', views.logout),
    path('profile/', views.ProfileView.as_view()),
    path('devices/', views.DeviceListView.as_view()),
    path('devices/register/', views.register_device),
    path('devices/<int:device_id>/remove/', views.remove_device),
    path('progress/', views.VideoProgressView.as_view()),
]
