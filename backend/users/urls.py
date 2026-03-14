from django.urls import path
from .views import RegisterView, LoginView, MeView

urlpatterns = [
    path('auth/register/', RegisterView.as_view(), name='auth_register'),
    path('auth/login/',    LoginView.as_view(),    name='auth_login'),
    path('auth/me/',       MeView.as_view(),       name='auth_me'),
]
