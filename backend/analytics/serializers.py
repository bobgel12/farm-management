from rest_framework import serializers
from .models import Dashboard, KPI, KPICalculation, AnalyticsQuery, Benchmark


class DashboardSerializer(serializers.ModelSerializer):
    """Serializer for Dashboard model"""
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = Dashboard
        fields = [
            'id', 'name', 'description', 'dashboard_type', 'layout_config',
            'default_filters', 'organization', 'organization_name',
            'is_public', 'is_active', 'created_by', 'created_by_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class KPISerializer(serializers.ModelSerializer):
    """Serializer for KPI model"""
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = KPI
        fields = [
            'id', 'name', 'description', 'kpi_type', 'metric_type',
            'calculation_config', 'unit', 'target_value',
            'warning_threshold', 'critical_threshold',
            'organization', 'organization_name', 'is_active', 'is_public',
            'created_by', 'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class KPICalculationSerializer(serializers.ModelSerializer):
    """Serializer for KPICalculation model"""
    kpi_name = serializers.CharField(source='kpi.name', read_only=True)
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    
    class Meta:
        model = KPICalculation
        fields = [
            'id', 'kpi', 'kpi_name', 'value', 'unit',
            'calculation_date', 'calculation_period_start', 'calculation_period_end',
            'filters', 'previous_value', 'change_percentage', 'status',
            'organization', 'organization_name', 'calculated_at', 'calculated_by'
        ]
        read_only_fields = ['id', 'calculated_at', 'change_percentage', 'status']


class AnalyticsQuerySerializer(serializers.ModelSerializer):
    """Serializer for AnalyticsQuery model"""
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = AnalyticsQuery
        fields = [
            'id', 'name', 'description', 'query_config',
            'organization', 'organization_name', 'created_by', 'created_by_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class BenchmarkSerializer(serializers.ModelSerializer):
    """Serializer for Benchmark model"""
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = Benchmark
        fields = [
            'id', 'name', 'description', 'benchmark_type', 'metric_name',
            'average_value', 'min_value', 'max_value',
            'percentile_25', 'percentile_75', 'unit',
            'period_start', 'period_end', 'filters',
            'organization', 'organization_name', 'is_active',
            'created_by', 'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

