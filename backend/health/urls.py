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
    path('health/simple/', views.simple_health_check, name='simple_health_check'),
    path('health/default-program/', views.default_program_check, name='default_program_check'),
]
