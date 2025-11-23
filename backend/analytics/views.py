from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .models import Dashboard, KPI, KPICalculation, AnalyticsQuery, Benchmark
from .serializers import (
    DashboardSerializer,
    KPISerializer,
    KPICalculationSerializer,
    AnalyticsQuerySerializer,
    BenchmarkSerializer
)


class DashboardViewSet(viewsets.ModelViewSet):
    """ViewSet for Dashboard management"""
    queryset = Dashboard.objects.all()
    serializer_class = DashboardSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter dashboards based on organization"""
        queryset = Dashboard.objects.filter(is_active=True)
        
        organization_id = self.request.query_params.get('organization_id')
        if organization_id:
            queryset = queryset.filter(organization_id=organization_id)
        
        dashboard_type = self.request.query_params.get('dashboard_type')
        if dashboard_type:
            queryset = queryset.filter(dashboard_type=dashboard_type)
        
        # Include public dashboards or user's organization dashboards
        if not self.request.user.is_staff:
            user_orgs = queryset.filter(
                organization__organization_users__user=self.request.user,
                organization__organization_users__is_active=True
            )
            public_dashboards = queryset.filter(is_public=True)
            queryset = (public_dashboards | user_orgs).distinct()
        
        return queryset
    
    def perform_create(self, serializer):
        """Set created_by when creating dashboard"""
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['get'])
    def data(self, request, pk=None):
        """Get dashboard data"""
        dashboard = self.get_object()
        
        # TODO: Implement dashboard data aggregation
        # This would fetch data based on dashboard configuration
        
        return Response({
            'dashboard_id': dashboard.id,
            'dashboard_name': dashboard.name,
            'data': {},
            'message': 'Dashboard data aggregation not yet implemented'
        })


class KPIViewSet(viewsets.ModelViewSet):
    """ViewSet for KPI management"""
    queryset = KPI.objects.all()
    serializer_class = KPISerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter KPIs based on organization"""
        queryset = KPI.objects.filter(is_active=True)
        
        organization_id = self.request.query_params.get('organization_id')
        if organization_id:
            queryset = queryset.filter(organization_id=organization_id)
        
        kpi_type = self.request.query_params.get('kpi_type')
        if kpi_type:
            queryset = queryset.filter(kpi_type=kpi_type)
        
        # Include public KPIs or user's organization KPIs
        if not self.request.user.is_staff:
            user_orgs = queryset.filter(
                organization__organization_users__user=self.request.user,
                organization__organization_users__is_active=True
            )
            public_kpis = queryset.filter(is_public=True)
            queryset = (public_kpis | user_orgs).distinct()
        
        return queryset
    
    def perform_create(self, serializer):
        """Set created_by when creating KPI"""
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def calculate(self, request, pk=None):
        """Calculate KPI value"""
        from analytics.services import KPICalculationService
        
        kpi = self.get_object()
        
        calculation_date = request.data.get('calculation_date')
        filters = request.data.get('filters', {})
        
        if calculation_date:
            from datetime import datetime
            calculation_date = datetime.strptime(calculation_date, '%Y-%m-%d').date()
        
        # Calculate KPI
        value = KPICalculationService.calculate_organization_kpi(
            kpi.organization,
            {
                'metric_type': kpi.metric_type,
                'calculation_config': kpi.calculation_config
            },
            calculation_date,
            filters
        )
        
        return Response({
            'kpi_id': kpi.id,
            'kpi_name': kpi.name,
            'value': value,
            'unit': kpi.unit,
            'calculation_date': calculation_date or timezone.now().date().isoformat()
        })


class KPICalculationViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for KPICalculation (read-only for historical data)"""
    queryset = KPICalculation.objects.all()
    serializer_class = KPICalculationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter calculations based on KPI and organization"""
        queryset = KPICalculation.objects.all()
        
        kpi_id = self.request.query_params.get('kpi_id')
        if kpi_id:
            queryset = queryset.filter(kpi_id=kpi_id)
        
        organization_id = self.request.query_params.get('organization_id')
        if organization_id:
            queryset = queryset.filter(organization_id=organization_id)
        
        return queryset.order_by('-calculation_date', 'kpi')


class AnalyticsQueryViewSet(viewsets.ModelViewSet):
    """ViewSet for AnalyticsQuery management"""
    queryset = AnalyticsQuery.objects.all()
    serializer_class = AnalyticsQuerySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter queries based on user and organization"""
        queryset = AnalyticsQuery.objects.all()
        
        organization_id = self.request.query_params.get('organization_id')
        if organization_id:
            queryset = queryset.filter(organization_id=organization_id)
        
        if not self.request.user.is_staff:
            queryset = queryset.filter(created_by=self.request.user)
        
        return queryset.order_by('-created_at')
    
    def perform_create(self, serializer):
        """Set created_by when creating query"""
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def execute(self, request, pk=None):
        """Execute an analytics query"""
        query = self.get_object()
        # TODO: Implement query execution
        return Response({'message': 'Query execution triggered'}, status=status.HTTP_202_ACCEPTED)
    
    @action(detail=False, methods=['post'])
    def trend_analysis(self, request):
        """Perform trend analysis"""
        from analytics.services import TrendAnalysisService
        from farms.models import Flock
        
        flock_id = request.data.get('flock_id')
        metric_type = request.data.get('metric_type', 'weight')
        period_days = request.data.get('period_days', 30)
        
        if not flock_id:
            return Response(
                {'error': 'flock_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            flock = Flock.objects.get(id=flock_id)
        except Flock.DoesNotExist:
            return Response(
                {'error': 'Flock not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        trend = TrendAnalysisService.analyze_flock_trend(flock, metric_type, period_days)
        
        if trend is None:
            return Response(
                {'error': 'Could not calculate trend'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response(trend)
    
    @action(detail=False, methods=['post'])
    def correlation_analysis(self, request):
        """Perform correlation analysis"""
        from analytics.services import CorrelationAnalysisService
        from farms.models import Flock
        
        flock_id = request.data.get('flock_id')
        metric1 = request.data.get('metric1', 'weight')
        metric2 = request.data.get('metric2', 'feed_consumption')
        period_days = request.data.get('period_days', 30)
        
        if not flock_id:
            return Response(
                {'error': 'flock_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            flock = Flock.objects.get(id=flock_id)
        except Flock.DoesNotExist:
            return Response(
                {'error': 'Flock not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        correlation = CorrelationAnalysisService.analyze_correlation(
            flock, metric1, metric2, period_days
        )
        
        if correlation is None:
            return Response(
                {'error': 'Could not calculate correlation'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response(correlation)


class BenchmarkViewSet(viewsets.ModelViewSet):
    """ViewSet for Benchmark management"""
    queryset = Benchmark.objects.all()
    serializer_class = BenchmarkSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter benchmarks based on organization"""
        queryset = Benchmark.objects.filter(is_active=True)
        
        organization_id = self.request.query_params.get('organization_id')
        if organization_id:
            queryset = queryset.filter(organization_id=organization_id)
        
        benchmark_type = self.request.query_params.get('benchmark_type')
        if benchmark_type:
            queryset = queryset.filter(benchmark_type=benchmark_type)
        
        metric_name = self.request.query_params.get('metric_name')
        if metric_name:
            queryset = queryset.filter(metric_name__icontains=metric_name)
        
        return queryset
    
    def perform_create(self, serializer):
        """Set created_by when creating benchmark"""
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def compare_flock(self, request, pk=None):
        """Compare a flock to this benchmark"""
        from analytics.services import BenchmarkingService
        from farms.models import Flock
        
        benchmark = self.get_object()
        flock_id = request.data.get('flock_id')
        
        if not flock_id:
            return Response(
                {'error': 'flock_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            flock = Flock.objects.get(id=flock_id)
        except Flock.DoesNotExist:
            return Response(
                {'error': 'Flock not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        comparison = BenchmarkingService.compare_flock_to_benchmark(flock, benchmark)
        
        if comparison is None:
            return Response(
                {'error': 'Could not calculate comparison'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response(comparison)
