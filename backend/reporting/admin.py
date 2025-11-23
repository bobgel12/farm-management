from django.contrib import admin
from .models import ReportTemplate, ScheduledReport, ReportExecution, ReportBuilderQuery


@admin.register(ReportTemplate)
class ReportTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'report_type', 'default_format', 'is_active', 'is_public', 'organization', 'created_by', 'created_at']
    list_filter = ['report_type', 'default_format', 'is_active', 'is_public', 'organization']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'report_type', 'organization')
        }),
        ('Configuration', {
            'fields': ('template_config', 'data_source')
        }),
        ('Formatting', {
            'fields': ('default_format', 'include_charts', 'include_summary')
        }),
        ('Visibility', {
            'fields': ('is_active', 'is_public', 'created_by')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(ScheduledReport)
class ScheduledReportAdmin(admin.ModelAdmin):
    list_display = ['name', 'template', 'frequency', 'status', 'next_run_at', 'last_run_at', 'organization', 'created_by']
    list_filter = ['frequency', 'status', 'organization']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    filter_horizontal = ['recipients']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'template', 'organization')
        }),
        ('Schedule', {
            'fields': ('frequency', 'schedule_config', 'next_run_at', 'last_run_at')
        }),
        ('Recipients', {
            'fields': ('recipients', 'email_recipients')
        }),
        ('Configuration', {
            'fields': ('report_filters', 'status')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at')
        }),
    )


@admin.register(ReportExecution)
class ReportExecutionAdmin(admin.ModelAdmin):
    list_display = ['template', 'status', 'export_format', 'started_at', 'completed_at', 'execution_time_seconds', 'organization']
    list_filter = ['status', 'export_format', 'organization']
    search_fields = ['template__name', 'error_message']
    readonly_fields = ['started_at', 'completed_at', 'execution_time_seconds']
    
    fieldsets = (
        ('Report Information', {
            'fields': ('scheduled_report', 'template', 'organization')
        }),
        ('Execution Details', {
            'fields': ('status', 'parameters', 'export_format', 'report_file')
        }),
        ('Timing', {
            'fields': ('started_at', 'completed_at', 'execution_time_seconds')
        }),
        ('Error Information', {
            'fields': ('error_message',)
        }),
        ('Metadata', {
            'fields': ('created_by',)
        }),
    )


@admin.register(ReportBuilderQuery)
class ReportBuilderQueryAdmin(admin.ModelAdmin):
    list_display = ['name', 'organization', 'created_by', 'created_at', 'updated_at']
    list_filter = ['organization']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'organization')
        }),
        ('Query Configuration', {
            'fields': ('query_config',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at')
        }),
    )

