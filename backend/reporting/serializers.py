from rest_framework import serializers
from .models import ReportTemplate, ScheduledReport, ReportExecution, ReportBuilderQuery


class ReportTemplateSerializer(serializers.ModelSerializer):
    """Serializer for ReportTemplate model"""
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    
    class Meta:
        model = ReportTemplate
        fields = [
            'id', 'name', 'description', 'report_type', 'template_config',
            'data_source', 'default_format', 'include_charts', 'include_summary',
            'organization', 'organization_name', 'is_active', 'is_public',
            'created_by', 'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ScheduledReportSerializer(serializers.ModelSerializer):
    """Serializer for ScheduledReport model"""
    template = ReportTemplateSerializer(read_only=True)
    template_id = serializers.IntegerField(write_only=True, required=False)
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = ScheduledReport
        fields = [
            'id', 'name', 'description', 'template', 'template_id',
            'frequency', 'schedule_config', 'recipients', 'email_recipients',
            'report_filters', 'status', 'next_run_at', 'last_run_at',
            'organization', 'organization_name', 'created_by', 'created_by_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'next_run_at', 'last_run_at']


class ReportExecutionSerializer(serializers.ModelSerializer):
    """Serializer for ReportExecution model"""
    template_name = serializers.CharField(source='template.name', read_only=True)
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    
    class Meta:
        model = ReportExecution
        fields = [
            'id', 'scheduled_report', 'template', 'template_name',
            'status', 'parameters', 'report_file', 'export_format',
            'started_at', 'completed_at', 'error_message', 'execution_time_seconds',
            'organization', 'organization_name', 'created_by'
        ]
        read_only_fields = ['id', 'started_at', 'completed_at', 'execution_time_seconds']


class ReportBuilderQuerySerializer(serializers.ModelSerializer):
    """Serializer for ReportBuilderQuery model"""
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = ReportBuilderQuery
        fields = [
            'id', 'name', 'description', 'query_config',
            'organization', 'organization_name', 'created_by', 'created_by_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

