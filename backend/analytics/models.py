"""
Analytics models for Business Intelligence, KPIs, and analytics dashboards
"""
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid


class Dashboard(models.Model):
    """Analytics dashboard configuration"""
    DASHBOARD_TYPE_CHOICES = [
        ('executive', 'Executive Dashboard'),
        ('operational', 'Operational Dashboard'),
        ('farm', 'Farm Dashboard'),
        ('house', 'House Dashboard'),
        ('flock', 'Flock Dashboard'),
        ('custom', 'Custom Dashboard'),
    ]
    
    # Dashboard information
    name = models.CharField(max_length=200, help_text="Dashboard name")
    description = models.TextField(blank=True)
    dashboard_type = models.CharField(
        max_length=50,
        choices=DASHBOARD_TYPE_CHOICES,
        help_text="Type of dashboard"
    )
    
    # Dashboard configuration
    layout_config = models.JSONField(
        default=dict,
        help_text="Dashboard layout configuration (widgets, positions, sizes)"
    )
    
    # Filters (applied by default)
    default_filters = models.JSONField(
        default=dict,
        help_text="Default filters (date range, farm, house, etc.)"
    )
    
    # Organization
    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        related_name='dashboards',
        null=True,
        blank=True,
        help_text="Organization this dashboard belongs to"
    )
    
    # Visibility
    is_public = models.BooleanField(
        default=False,
        help_text="Whether dashboard is available to all organization users"
    )
    is_active = models.BooleanField(default=True)
    
    # Metadata
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_dashboards'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Dashboard'
        verbose_name_plural = 'Dashboards'
        indexes = [
            models.Index(fields=['dashboard_type', 'is_active']),
            models.Index(fields=['organization', 'is_active']),
        ]
    
    def __str__(self):
        return self.name


class KPI(models.Model):
    """Key Performance Indicator definition"""
    KPI_TYPE_CHOICES = [
        ('flock_performance', 'Flock Performance'),
        ('farm_efficiency', 'Farm Efficiency'),
        ('cost_management', 'Cost Management'),
        ('growth', 'Growth'),
        ('health', 'Health'),
        ('productivity', 'Productivity'),
        ('custom', 'Custom'),
    ]
    
    METRIC_TYPE_CHOICES = [
        ('count', 'Count'),
        ('sum', 'Sum'),
        ('average', 'Average'),
        ('percentage', 'Percentage'),
        ('ratio', 'Ratio'),
        ('trend', 'Trend'),
        ('comparison', 'Comparison'),
    ]
    
    # KPI information
    name = models.CharField(max_length=200, help_text="KPI name")
    description = models.TextField(blank=True)
    kpi_type = models.CharField(
        max_length=50,
        choices=KPI_TYPE_CHOICES,
        help_text="Type of KPI"
    )
    metric_type = models.CharField(
        max_length=20,
        choices=METRIC_TYPE_CHOICES,
        help_text="Metric calculation type"
    )
    
    # Calculation configuration
    calculation_config = models.JSONField(
        default=dict,
        help_text="KPI calculation configuration (formula, data source, filters)"
    )
    
    # Display configuration
    unit = models.CharField(
        max_length=50,
        blank=True,
        help_text="Unit of measurement (e.g., %, kg, days)"
    )
    target_value = models.FloatField(
        null=True, blank=True,
        help_text="Target value for this KPI"
    )
    warning_threshold = models.FloatField(
        null=True, blank=True,
        help_text="Warning threshold (below/above this triggers warning)"
    )
    critical_threshold = models.FloatField(
        null=True, blank=True,
        help_text="Critical threshold (below/above this triggers critical alert)"
    )
    
    # Organization
    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        related_name='kpis',
        null=True,
        blank=True
    )
    
    # Metadata
    is_active = models.BooleanField(default=True)
    is_public = models.BooleanField(
        default=False,
        help_text="Whether KPI is available to all organization users"
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_kpis'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['kpi_type', 'name']
        verbose_name = 'KPI'
        verbose_name_plural = 'KPIs'
        indexes = [
            models.Index(fields=['kpi_type', 'is_active']),
            models.Index(fields=['organization', 'is_active']),
        ]
    
    def __str__(self):
        return self.name


class KPICalculation(models.Model):
    """Historical KPI calculations"""
    kpi = models.ForeignKey(
        KPI,
        on_delete=models.CASCADE,
        related_name='calculations',
        help_text="KPI this calculation belongs to"
    )
    
    # Calculation result
    value = models.FloatField(help_text="Calculated KPI value")
    unit = models.CharField(max_length=50, blank=True)
    
    # Context
    calculation_date = models.DateField(help_text="Date this calculation is for")
    calculation_period_start = models.DateField(
        null=True, blank=True,
        help_text="Start of calculation period"
    )
    calculation_period_end = models.DateField(
        null=True, blank=True,
        help_text="End of calculation period"
    )
    
    # Filters applied
    filters = models.JSONField(
        default=dict,
        help_text="Filters applied during calculation (farm, house, flock, etc.)"
    )
    
    # Comparison
    previous_value = models.FloatField(
        null=True, blank=True,
        help_text="Previous period value for comparison"
    )
    change_percentage = models.FloatField(
        null=True, blank=True,
        help_text="Percentage change from previous period"
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=[
            ('normal', 'Normal'),
            ('warning', 'Warning'),
            ('critical', 'Critical'),
        ],
        default='normal',
        help_text="Status based on thresholds"
    )
    
    # Organization
    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        related_name='kpi_calculations',
        null=True,
        blank=True
    )
    
    # Metadata
    calculated_at = models.DateTimeField(auto_now_add=True)
    calculated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='kpi_calculations'
    )
    
    class Meta:
        ordering = ['-calculation_date', 'kpi']
        verbose_name = 'KPI Calculation'
        verbose_name_plural = 'KPI Calculations'
        unique_together = ['kpi', 'calculation_date', 'organization', 'filters']
        indexes = [
            models.Index(fields=['kpi', '-calculation_date']),
            models.Index(fields=['organization', '-calculation_date']),
            models.Index(fields=['status', '-calculation_date']),
        ]
    
    def __str__(self):
        return f"{self.kpi.name} - {self.calculation_date} ({self.value} {self.unit})"


class AnalyticsQuery(models.Model):
    """Saved analytics queries"""
    name = models.CharField(max_length=200, help_text="Query name")
    description = models.TextField(blank=True)
    
    # Query configuration
    query_config = models.JSONField(
        default=dict,
        help_text="Query configuration (metrics, dimensions, filters, aggregations)"
    )
    
    # Organization
    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        related_name='analytics_queries',
        null=True,
        blank=True
    )
    
    # Metadata
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='analytics_queries'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Analytics Query'
        verbose_name_plural = 'Analytics Queries'
    
    def __str__(self):
        return self.name


class Benchmark(models.Model):
    """Benchmark data for comparison"""
    BENCHMARK_TYPE_CHOICES = [
        ('industry', 'Industry Benchmark'),
        ('organization', 'Organization Benchmark'),
        ('farm', 'Farm Benchmark'),
        ('breed', 'Breed Benchmark'),
        ('custom', 'Custom Benchmark'),
    ]
    
    # Benchmark information
    name = models.CharField(max_length=200, help_text="Benchmark name")
    description = models.TextField(blank=True)
    benchmark_type = models.CharField(
        max_length=50,
        choices=BENCHMARK_TYPE_CHOICES,
        help_text="Type of benchmark"
    )
    
    # Benchmark values
    metric_name = models.CharField(max_length=200, help_text="Metric name (e.g., FCR, Mortality Rate)")
    average_value = models.FloatField(help_text="Average benchmark value")
    min_value = models.FloatField(null=True, blank=True, help_text="Minimum benchmark value")
    max_value = models.FloatField(null=True, blank=True, help_text="Maximum benchmark value")
    percentile_25 = models.FloatField(null=True, blank=True, help_text="25th percentile")
    percentile_75 = models.FloatField(null=True, blank=True, help_text="75th percentile")
    
    # Context
    unit = models.CharField(max_length=50, blank=True, help_text="Unit of measurement")
    period_start = models.DateField(null=True, blank=True, help_text="Period start date")
    period_end = models.DateField(null=True, blank=True, help_text="Period end date")
    
    # Filters
    filters = models.JSONField(
        default=dict,
        help_text="Filters applied (breed, region, farm type, etc.)"
    )
    
    # Organization
    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        related_name='benchmarks',
        null=True,
        blank=True
    )
    
    # Metadata
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_benchmarks'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['benchmark_type', 'metric_name']
        verbose_name = 'Benchmark'
        verbose_name_plural = 'Benchmarks'
        indexes = [
            models.Index(fields=['benchmark_type', 'metric_name']),
            models.Index(fields=['organization', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.metric_name} - {self.name}"

