from django.urls import path
from . import views

urlpatterns = [
    path('auth/login/', views.login_view, name='login'),
    path('auth/logout/', views.logout_view, name='logout'),
    path('auth/user/', views.user_info, name='user-info'),
    path('auth/check/', views.check_auth, name='check-auth'),
    path('auth/request-password-reset/', views.request_password_reset, name='request-password-reset'),
    path('auth/reset-password/', views.reset_password, name='reset-password'),
    path('auth/change-password/', views.change_password, name='change-password'),
]
