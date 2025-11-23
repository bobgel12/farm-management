from django.contrib import admin
from .models import Dashboard, KPI, KPICalculation, AnalyticsQuery, Benchmark


@admin.register(Dashboard)
class DashboardAdmin(admin.ModelAdmin):
    list_display = ['name', 'dashboard_type', 'is_active', 'is_public', 'organization', 'created_by', 'created_at']
    list_filter = ['dashboard_type', 'is_active', 'is_public', 'organization']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'dashboard_type', 'organization')
        }),
        ('Configuration', {
            'fields': ('layout_config', 'default_filters')
        }),
        ('Visibility', {
            'fields': ('is_active', 'is_public', 'created_by')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(KPI)
class KPIAdmin(admin.ModelAdmin):
    list_display = ['name', 'kpi_type', 'metric_type', 'unit', 'target_value', 'is_active', 'organization', 'created_by']
    list_filter = ['kpi_type', 'metric_type', 'is_active', 'is_public', 'organization']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'kpi_type', 'metric_type', 'organization')
        }),
        ('Calculation', {
            'fields': ('calculation_config',)
        }),
        ('Display', {
            'fields': ('unit', 'target_value', 'warning_threshold', 'critical_threshold')
        }),
        ('Visibility', {
            'fields': ('is_active', 'is_public', 'created_by')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(KPICalculation)
class KPICalculationAdmin(admin.ModelAdmin):
    list_display = ['kpi', 'value', 'unit', 'calculation_date', 'status', 'change_percentage', 'organization', 'calculated_at']
    list_filter = ['status', 'organization']
    search_fields = ['kpi__name']
    readonly_fields = ['calculated_at']
    
    fieldsets = (
        ('KPI Information', {
            'fields': ('kpi', 'organization')
        }),
        ('Calculation Result', {
            'fields': ('value', 'unit', 'status')
        }),
        ('Period', {
            'fields': ('calculation_date', 'calculation_period_start', 'calculation_period_end')
        }),
        ('Context', {
            'fields': ('filters',)
        }),
        ('Comparison', {
            'fields': ('previous_value', 'change_percentage')
        }),
        ('Metadata', {
            'fields': ('calculated_at', 'calculated_by')
        }),
    )


@admin.register(AnalyticsQuery)
class AnalyticsQueryAdmin(admin.ModelAdmin):
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


@admin.register(Benchmark)
class BenchmarkAdmin(admin.ModelAdmin):
    list_display = ['name', 'benchmark_type', 'metric_name', 'average_value', 'unit', 'is_active', 'organization', 'created_by']
    list_filter = ['benchmark_type', 'is_active', 'organization']
    search_fields = ['name', 'metric_name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'benchmark_type', 'metric_name', 'organization')
        }),
        ('Values', {
            'fields': ('average_value', 'min_value', 'max_value', 'percentile_25', 'percentile_75', 'unit')
        }),
        ('Period', {
            'fields': ('period_start', 'period_end')
        }),
        ('Filters', {
            'fields': ('filters',)
        }),
        ('Status', {
            'fields': ('is_active', 'created_by')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )

