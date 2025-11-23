"""
Reporting models for custom reports, templates, and scheduled reports
"""
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid
import json


class ReportTemplate(models.Model):
    """Template for custom reports"""
    REPORT_TYPE_CHOICES = [
        ('flock_performance', 'Flock Performance'),
        ('farm_summary', 'Farm Summary'),
        ('house_status', 'House Status'),
        ('task_completion', 'Task Completion'),
        ('financial', 'Financial'),
        ('custom', 'Custom'),
    ]
    
    EXPORT_FORMAT_CHOICES = [
        ('pdf', 'PDF'),
        ('excel', 'Excel (XLSX)'),
        ('csv', 'CSV'),
        ('json', 'JSON'),
        ('html', 'HTML'),
    ]
    
    # Template information
    name = models.CharField(max_length=200, help_text="Template name")
    description = models.TextField(blank=True, help_text="Template description")
    report_type = models.CharField(
        max_length=50,
        choices=REPORT_TYPE_CHOICES,
        help_text="Type of report"
    )
    
    # Template configuration
    template_config = models.JSONField(
        default=dict,
        help_text="Report template configuration (filters, fields, formatting)"
    )
    
    # Data source configuration
    data_source = models.JSONField(
        default=dict,
        help_text="Data source configuration (models, fields, filters)"
    )
    
    # Formatting options
    default_format = models.CharField(
        max_length=20,
        choices=EXPORT_FORMAT_CHOICES,
        default='pdf',
        help_text="Default export format"
    )
    include_charts = models.BooleanField(
        default=True,
        help_text="Include charts/graphs in report"
    )
    include_summary = models.BooleanField(
        default=True,
        help_text="Include summary section"
    )
    
    # Organization/scope
    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        related_name='report_templates',
        null=True,
        blank=True,
        help_text="Organization this template belongs to (null for global templates)"
    )
    
    # Metadata
    is_active = models.BooleanField(default=True)
    is_public = models.BooleanField(
        default=False,
        help_text="Whether template is available to all organizations"
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_report_templates'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Report Template'
        verbose_name_plural = 'Report Templates'
        indexes = [
            models.Index(fields=['report_type', 'is_active']),
            models.Index(fields=['organization', 'is_active']),
        ]
    
    def __str__(self):
        return self.name


class ScheduledReport(models.Model):
    """Scheduled report configuration"""
    FREQUENCY_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
        ('custom', 'Custom'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    # Report configuration
    name = models.CharField(max_length=200, help_text="Scheduled report name")
    description = models.TextField(blank=True)
    template = models.ForeignKey(
        ReportTemplate,
        on_delete=models.CASCADE,
        related_name='scheduled_reports',
        help_text="Report template to use"
    )
    
    # Schedule configuration
    frequency = models.CharField(
        max_length=20,
        choices=FREQUENCY_CHOICES,
        help_text="Report frequency"
    )
    schedule_config = models.JSONField(
        default=dict,
        help_text="Schedule configuration (day of week, day of month, time, etc.)"
    )
    
    # Recipients
    recipients = models.ManyToManyField(
        User,
        related_name='scheduled_reports',
        help_text="Users who will receive this report"
    )
    email_recipients = models.JSONField(
        default=list,
        help_text="Additional email recipients (list of email addresses)"
    )
    
    # Filters (applied to each report generation)
    report_filters = models.JSONField(
        default=dict,
        help_text="Filters to apply to each report (date range, farm, house, etc.)"
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        help_text="Schedule status"
    )
    
    # Next run tracking
    next_run_at = models.DateTimeField(
        null=True, blank=True,
        help_text="Next scheduled run time"
    )
    last_run_at = models.DateTimeField(
        null=True, blank=True,
        help_text="Last run time"
    )
    
    # Organization
    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        related_name='scheduled_reports',
        null=True,
        blank=True
    )
    
    # Metadata
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_scheduled_reports'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['next_run_at', 'name']
        verbose_name = 'Scheduled Report'
        verbose_name_plural = 'Scheduled Reports'
        indexes = [
            models.Index(fields=['status', 'next_run_at']),
            models.Index(fields=['organization', 'status']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.frequency})"


class ReportExecution(models.Model):
    """Report execution history"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Report reference
    scheduled_report = models.ForeignKey(
        ScheduledReport,
        on_delete=models.CASCADE,
        related_name='executions',
        null=True,
        blank=True,
        help_text="Scheduled report that triggered this execution"
    )
    template = models.ForeignKey(
        ReportTemplate,
        on_delete=models.CASCADE,
        related_name='executions',
        help_text="Report template used"
    )
    
    # Execution details
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        help_text="Execution status"
    )
    
    # Report parameters
    parameters = models.JSONField(
        default=dict,
        help_text="Report parameters (filters, date range, etc.)"
    )
    
    # Output
    report_file = models.FileField(
        upload_to='reports/',
        null=True, blank=True,
        help_text="Generated report file"
    )
    export_format = models.CharField(
        max_length=20,
        choices=ReportTemplate.EXPORT_FORMAT_CHOICES,
        default='pdf'
    )
    
    # Execution metadata
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True, help_text="Error message if execution failed")
    execution_time_seconds = models.FloatField(
        null=True, blank=True,
        help_text="Report generation time in seconds"
    )
    
    # Organization
    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        related_name='report_executions',
        null=True,
        blank=True
    )
    
    # Metadata
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='report_executions'
    )
    
    class Meta:
        ordering = ['-started_at']
        verbose_name = 'Report Execution'
        verbose_name_plural = 'Report Executions'
        indexes = [
            models.Index(fields=['status', '-started_at']),
            models.Index(fields=['scheduled_report', '-started_at']),
            models.Index(fields=['organization', '-started_at']),
        ]
    
    def __str__(self):
        return f"{self.template.name} - {self.started_at.strftime('%Y-%m-%d %H:%M')} ({self.status})"


class ReportBuilderQuery(models.Model):
    """Saved queries for report builder"""
    name = models.CharField(max_length=200, help_text="Query name")
    description = models.TextField(blank=True)
    
    # Query configuration
    query_config = models.JSONField(
        default=dict,
        help_text="Query configuration (models, fields, filters, aggregations)"
    )
    
    # Organization
    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        related_name='report_queries',
        null=True,
        blank=True
    )
    
    # Metadata
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='report_queries'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Report Builder Query'
        verbose_name_plural = 'Report Builder Queries'
    
    def __str__(self):
        return self.name

