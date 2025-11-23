from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'dashboards', views.DashboardViewSet, basename='dashboard')
router.register(r'kpis', views.KPIViewSet, basename='kpi')
router.register(r'kpi-calculations', views.KPICalculationViewSet, basename='kpi-calculation')
router.register(r'analytics-queries', views.AnalyticsQueryViewSet, basename='analytics-query')
router.register(r'benchmarks', views.BenchmarkViewSet, basename='benchmark')

urlpatterns = [
    path('', include(router.urls)),
]

