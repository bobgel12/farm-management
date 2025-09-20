"""
Health check URL patterns
"""
from django.urls import path
from . import views

urlpatterns = [
    path('health/', views.health_check, name='health_check'),
    path('health/detailed/', views.detailed_health_check, name='detailed_health_check'),
    path('health/ready/', views.readiness_check, name='readiness_check'),
    path('health/alive/', views.liveness_check, name='liveness_check'),
]
