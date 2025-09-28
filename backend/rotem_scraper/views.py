from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from .models import RotemDataPoint, MLPrediction, MLModel, RotemController, RotemFarm, RotemUser, RotemScrapeLog
from .serializers import (
    RotemDataPointSerializer, MLPredictionSerializer, MLModelSerializer, RotemControllerSerializer,
    RotemFarmSerializer, RotemUserSerializer, RotemScrapeLogSerializer
)
from .services.scraper_service import DjangoRotemScraperService
from .services.ml_service import MLAnalysisService
from django.utils import timezone
from datetime import timedelta


class RotemDataViewSet(viewsets.ReadOnlyModelViewSet):
    """API for Rotem data visualization"""
    queryset = RotemDataPoint.objects.all()
    serializer_class = RotemDataPointSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['data_type', 'controller', 'quality']
    search_fields = ['data_type', 'unit']
    ordering_fields = ['timestamp', 'value']
    ordering = ['-timestamp']
    
    def get_queryset(self):
        """Filter queryset based on query parameters"""
        queryset = super().get_queryset()
        
        # Filter by farm_id if provided
        farm_id = self.request.query_params.get('farm_id')
        if farm_id:
            try:
                farm = RotemFarm.objects.get(farm_id=farm_id)
                controllers = farm.controllers.all()
                queryset = queryset.filter(controller__in=controllers)
            except RotemFarm.DoesNotExist:
                queryset = queryset.none()
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def latest_data(self, request):
        """Get latest data points for all controllers"""
        latest_data = RotemDataPoint.objects.filter(
            timestamp__gte=timezone.now() - timedelta(hours=1)
        ).order_by('-timestamp')
        
        serializer = self.get_serializer(latest_data, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Get recent data points for all controllers (last 24 hours)"""
        recent_data = RotemDataPoint.objects.filter(
            timestamp__gte=timezone.now() - timedelta(hours=24)
        ).order_by('-timestamp')
        
        serializer = self.get_serializer(recent_data, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def controller_data(self, request):
        """Get data for specific controller"""
        controller_id = request.query_params.get('controller_id')
        if not controller_id:
            return Response({'error': 'controller_id parameter required'}, status=status.HTTP_400_BAD_REQUEST)
        
        data = RotemDataPoint.objects.filter(
            controller_id=controller_id,
            timestamp__gte=timezone.now() - timedelta(days=7)
        ).order_by('timestamp')
        
        serializer = self.get_serializer(data, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_farm(self, request):
        """Get data points for a specific farm"""
        farm_id = request.query_params.get('farm_id')
        if not farm_id:
            return Response({'error': 'farm_id parameter required'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        try:
            farm = RotemFarm.objects.get(farm_id=farm_id)
            controllers = farm.controllers.all()
            data_points = self.queryset.filter(controller__in=controllers)
            serializer = self.get_serializer(data_points, many=True)
            return Response(serializer.data)
        except RotemFarm.DoesNotExist:
            return Response({'error': 'Farm not found'}, 
                          status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get data summary by farm"""
        farms = RotemFarm.objects.filter(is_active=True)
        summary = []
        
        for farm in farms:
            controllers = farm.controllers.all()
            total_points = self.queryset.filter(controller__in=controllers).count()
            recent_points = self.queryset.filter(
                controller__in=controllers,
                timestamp__gte=timezone.now() - timedelta(hours=24)
            ).count()
            
            summary.append({
                'farm_id': farm.farm_id,
                'farm_name': farm.farm_name,
                'total_data_points': total_points,
                'recent_data_points': recent_points,
                'controllers': controllers.count()
            })
        
        return Response(summary)


class MLPredictionViewSet(viewsets.ReadOnlyModelViewSet):
    """API for ML predictions and insights"""
    queryset = MLPrediction.objects.filter(is_active=True)
    serializer_class = MLPredictionSerializer
    
    @action(detail=False, methods=['get'])
    def active_predictions(self, request):
        """Get active predictions"""
        predictions = self.queryset.filter(
            predicted_at__gte=timezone.now() - timedelta(hours=24)
        ).order_by('-predicted_at')
        
        serializer = self.get_serializer(predictions, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def anomalies(self, request):
        """Get anomaly predictions"""
        anomalies = self.queryset.filter(
            prediction_type='anomaly',
            predicted_at__gte=timezone.now() - timedelta(hours=24)
        ).order_by('-confidence_score')
        
        serializer = self.get_serializer(anomalies, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def failures(self, request):
        """Get failure predictions"""
        failures = self.queryset.filter(
            prediction_type='failure',
            predicted_at__gte=timezone.now() - timedelta(hours=24)
        ).order_by('-confidence_score')
        
        serializer = self.get_serializer(failures, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def optimizations(self, request):
        """Get optimization suggestions"""
        optimizations = self.queryset.filter(
            prediction_type='optimization',
            predicted_at__gte=timezone.now() - timedelta(hours=24)
        ).order_by('-predicted_at')
        
        serializer = self.get_serializer(optimizations, many=True)
        return Response(serializer.data)


class RotemControllerViewSet(viewsets.ReadOnlyModelViewSet):
    """API for Rotem controllers"""
    queryset = RotemController.objects.all()
    serializer_class = RotemControllerSerializer


class RotemFarmViewSet(viewsets.ReadOnlyModelViewSet):
    """API for Rotem farms"""
    queryset = RotemFarm.objects.all()
    serializer_class = RotemFarmSerializer
    lookup_field = 'farm_id'


class RotemUserViewSet(viewsets.ReadOnlyModelViewSet):
    """API for Rotem users"""
    queryset = RotemUser.objects.all()
    serializer_class = RotemUserSerializer


class RotemScrapeLogViewSet(viewsets.ReadOnlyModelViewSet):
    """API for Rotem scrape logs"""
    queryset = RotemScrapeLog.objects.all()
    serializer_class = RotemScrapeLogSerializer
    
    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Get recent scrape logs"""
        logs = self.queryset.order_by('-started_at')[:10]
        data = []
        for log in logs:
            data.append({
                'scrape_id': str(log.scrape_id),
                'started_at': log.started_at,
                'completed_at': log.completed_at,
                'status': log.status,
                'data_points_collected': log.data_points_collected,
                'error_message': log.error_message
            })
        return Response(data)


class RotemScraperViewSet(viewsets.ViewSet):
    """API endpoint for scraper operations"""
    
    @action(detail=False, methods=['post'])
    def scrape_farm(self, request):
        """Trigger scraping for a specific farm"""
        farm_id = request.data.get('farm_id')
        if not farm_id:
            return Response({'error': 'farm_id required'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        try:
            service = DjangoRotemScraperService(farm_id=farm_id)
            result = service.scrape_and_save_data()
            
            return Response({
                'status': result.status,
                'data_points_collected': result.data_points_collected,
                'completed_at': result.completed_at,
                'error_message': result.error_message
            })
        except Exception as e:
            return Response({'error': str(e)}, 
                          status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def scrape_all(self, request):
        """Trigger scraping for all farms"""
        try:
            service = DjangoRotemScraperService()
            results = service.scrape_all_farms()
            
            return Response({
                'results': results,
                'total_farms': len(results)
            })
        except Exception as e:
            return Response({'error': str(e)}, 
                          status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MLPredictionViewSet(viewsets.ReadOnlyModelViewSet):
    """API for ML predictions and insights"""
    queryset = MLPrediction.objects.filter(is_active=True)
    serializer_class = MLPredictionSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['prediction_type', 'controller', 'is_active']
    search_fields = ['prediction_type', 'controller__controller_name']
    ordering_fields = ['predicted_at', 'confidence_score']
    ordering = ['-predicted_at']
    
    @action(detail=False, methods=['get'])
    def active_predictions(self, request):
        """Get active predictions from last 24 hours"""
        predictions = self.queryset.filter(
            predicted_at__gte=timezone.now() - timedelta(hours=24)
        ).order_by('-predicted_at')
        
        serializer = self.get_serializer(predictions, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def anomalies(self, request):
        """Get anomaly predictions"""
        anomalies = self.queryset.filter(
            prediction_type='anomaly',
            predicted_at__gte=timezone.now() - timedelta(hours=24)
        ).order_by('-confidence_score')
        
        serializer = self.get_serializer(anomalies, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def failures(self, request):
        """Get equipment failure predictions"""
        failures = self.queryset.filter(
            prediction_type='failure',
            predicted_at__gte=timezone.now() - timedelta(days=7)
        ).order_by('-confidence_score')
        
        serializer = self.get_serializer(failures, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def optimizations(self, request):
        """Get environmental optimization suggestions"""
        optimizations = self.queryset.filter(
            prediction_type='optimization',
            predicted_at__gte=timezone.now() - timedelta(hours=24)
        ).order_by('-predicted_at')
        
        serializer = self.get_serializer(optimizations, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def performance(self, request):
        """Get system performance analysis"""
        performance = self.queryset.filter(
            prediction_type='performance',
            predicted_at__gte=timezone.now() - timedelta(hours=24)
        ).order_by('-predicted_at')
        
        serializer = self.get_serializer(performance, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get ML predictions summary"""
        now = timezone.now()
        last_24h = now - timedelta(hours=24)
        last_7d = now - timedelta(days=7)
        
        summary = {
            'total_predictions': self.queryset.count(),
            'last_24h': {
                'total': self.queryset.filter(predicted_at__gte=last_24h).count(),
                'anomalies': self.queryset.filter(
                    prediction_type='anomaly', 
                    predicted_at__gte=last_24h
                ).count(),
                'failures': self.queryset.filter(
                    prediction_type='failure', 
                    predicted_at__gte=last_24h
                ).count(),
                'optimizations': self.queryset.filter(
                    prediction_type='optimization', 
                    predicted_at__gte=last_24h
                ).count(),
                'performance': self.queryset.filter(
                    prediction_type='performance', 
                    predicted_at__gte=last_24h
                ).count(),
            },
            'last_7d': {
                'total': self.queryset.filter(predicted_at__gte=last_7d).count(),
                'failures': self.queryset.filter(
                    prediction_type='failure', 
                    predicted_at__gte=last_7d
                ).count(),
            },
            'high_confidence_predictions': self.queryset.filter(
                confidence_score__gte=0.8,
                predicted_at__gte=last_24h
            ).count()
        }
        
        return Response(summary)


class MLModelViewSet(viewsets.ReadOnlyModelViewSet):
    """API for ML model information"""
    queryset = MLModel.objects.filter(is_active=True)
    serializer_class = MLModelSerializer
    
    @action(detail=False, methods=['post'])
    def train_models(self, request):
        """Trigger ML model training"""
        try:
            from .tasks import train_ml_models
            task = train_ml_models.delay()
            
            return Response({
                'message': 'Model training started',
                'task_id': task.id
            })
        except Exception as e:
            return Response({'error': str(e)}, 
                          status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def run_analysis(self, request):
        """Trigger ML analysis"""
        try:
            from .tasks import analyze_data
            task = analyze_data.delay()
            
            return Response({
                'message': 'ML analysis started',
                'task_id': task.id
            })
        except Exception as e:
            return Response({'error': str(e)}, 
                          status=status.HTTP_500_INTERNAL_SERVER_ERROR)