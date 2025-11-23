from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'report-templates', views.ReportTemplateViewSet, basename='report-template')
router.register(r'scheduled-reports', views.ScheduledReportViewSet, basename='scheduled-report')
router.register(r'report-executions', views.ReportExecutionViewSet, basename='report-execution')
router.register(r'report-queries', views.ReportBuilderQueryViewSet, basename='report-query')

urlpatterns = [
    path('', include(router.urls)),
]

