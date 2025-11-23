from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import ReportTemplate, ScheduledReport, ReportExecution, ReportBuilderQuery
from .serializers import (
    ReportTemplateSerializer,
    ScheduledReportSerializer,
    ReportExecutionSerializer,
    ReportBuilderQuerySerializer
)


class ReportTemplateViewSet(viewsets.ModelViewSet):
    """ViewSet for ReportTemplate management"""
    queryset = ReportTemplate.objects.all()
    serializer_class = ReportTemplateSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter templates based on organization"""
        queryset = ReportTemplate.objects.filter(is_active=True)
        
        organization_id = self.request.query_params.get('organization_id')
        if organization_id:
            queryset = queryset.filter(organization_id=organization_id)
        
        # Include public templates or user's organization templates
        if not self.request.user.is_staff:
            user_orgs = queryset.filter(
                organization__organization_users__user=self.request.user,
                organization__organization_users__is_active=True
            )
            public_templates = queryset.filter(is_public=True)
            queryset = (public_templates | user_orgs).distinct()
        
        return queryset
    
    def perform_create(self, serializer):
        """Set created_by when creating template"""
        serializer.save(created_by=self.request.user)


class ScheduledReportViewSet(viewsets.ModelViewSet):
    """ViewSet for ScheduledReport management"""
    queryset = ScheduledReport.objects.all()
    serializer_class = ScheduledReportSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter scheduled reports based on organization"""
        queryset = ScheduledReport.objects.all()
        
        organization_id = self.request.query_params.get('organization_id')
        if organization_id:
            queryset = queryset.filter(organization_id=organization_id)
        
        if not self.request.user.is_staff:
            queryset = queryset.filter(
                organization__organization_users__user=self.request.user,
                organization__organization_users__is_active=True
            ).distinct()
        
        return queryset
    
    def perform_create(self, serializer):
        """Set created_by when creating scheduled report"""
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def run_now(self, request, pk=None):
        """Trigger a scheduled report to run immediately"""
        scheduled_report = self.get_object()
        # TODO: Implement report generation
        return Response({'message': 'Report generation triggered'}, status=status.HTTP_202_ACCEPTED)


class ReportExecutionViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for ReportExecution (read-only for now)"""
    queryset = ReportExecution.objects.all()
    serializer_class = ReportExecutionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter executions based on organization"""
        queryset = ReportExecution.objects.all()
        
        organization_id = self.request.query_params.get('organization_id')
        if organization_id:
            queryset = queryset.filter(organization_id=organization_id)
        
        scheduled_report_id = self.request.query_params.get('scheduled_report_id')
        if scheduled_report_id:
            queryset = queryset.filter(scheduled_report_id=scheduled_report_id)
        
        return queryset.order_by('-started_at')


class ReportBuilderQueryViewSet(viewsets.ModelViewSet):
    """ViewSet for ReportBuilderQuery management"""
    queryset = ReportBuilderQuery.objects.all()
    serializer_class = ReportBuilderQuerySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter queries based on user and organization"""
        queryset = ReportBuilderQuery.objects.all()
        
        organization_id = self.request.query_params.get('organization_id')
        if organization_id:
            queryset = queryset.filter(organization_id=organization_id)
        
        if not self.request.user.is_staff:
            queryset = queryset.filter(created_by=self.request.user)
        
        return queryset.order_by('-created_at')
    
    def perform_create(self, serializer):
        """Set created_by when creating query"""
        serializer.save(created_by=self.request.user)

