from rest_framework import viewsets, status, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from .models import RotemDataPoint, MLPrediction, MLModel, RotemController, RotemFarm, RotemUser, RotemScrapeLog, RotemDailySummary
from .serializers import (
    RotemDataPointSerializer, MLPredictionSerializer, MLModelSerializer, RotemControllerSerializer,
    RotemFarmSerializer, RotemUserSerializer, RotemScrapeLogSerializer, RotemDailySummarySerializer,
    IntegratedFarmSerializer
)
from .services.scraper_service import DjangoRotemScraperService
from .services.ml_service import MLAnalysisService
from farms.models import Farm
from farms.views import user_accessible_organization_ids
from houses.models import House
from django.utils import timezone
from datetime import timedelta
import datetime as _dt
import logging

logger = logging.getLogger(__name__)


def _safe_float(value):
    if value is None:
        return None
    try:
        if isinstance(value, str):
            value = value.strip().replace(",", "")
            if value in {"", "- - -", "N/A", "---", "null"}:
                return None
        return float(value)
    except (ValueError, TypeError):
        return None


def _parse_rotem_history_rows(raw_command_data):
    """Normalize dsData.Data rows from RNBL_GetCommandData history commands."""
    response_obj = raw_command_data.get('reponseObj', raw_command_data) if isinstance(raw_command_data, dict) else {}
    ds_data = response_obj.get('dsData', {}) if isinstance(response_obj, dict) else {}
    return ds_data.get('Data', []) if isinstance(ds_data, dict) else []


def _rotem_history_command_payload(house, command_id: str):
    from .scraper import RotemScraper

    if not house.farm or not house.farm.rotem_username or not house.farm.rotem_password:
        return None, "Farm Rotem credentials are not configured."

    scraper = RotemScraper(username=house.farm.rotem_username, password=house.farm.rotem_password)
    if not scraper.login():
        return None, "Failed to authenticate with Rotem API"

    raw = scraper.get_command_data(house_number=house.house_number, command_id=command_id) or {}
    rows = _parse_rotem_history_rows(raw)
    return rows, None


def _parse_water_history_raw(raw_water_data, house) -> list:
    """
    Parse a raw Rotem CommandID 40 response into a sorted list of dicts with
    keys: growth_day, date (ISO string), consumption_avg.

    Shared by the per-house water_history action and the farm-level
    farm_water_compare view so that parsing logic lives in one place.
    """
    if not raw_water_data:
        return []

    water_history = []
    response_obj = raw_water_data.get('reponseObj', raw_water_data) if isinstance(raw_water_data, dict) else {}

    history_data = None
    if 'WaterHistory' in response_obj:
        history_data = response_obj['WaterHistory']
    elif 'ConsumptionHistory' in response_obj:
        history_data = response_obj['ConsumptionHistory']
    elif isinstance(response_obj.get('History'), dict) and 'Water' in response_obj['History']:
        history_data = response_obj['History']['Water']
    elif 'dsData' in response_obj:
        ds_data = response_obj['dsData']
        if isinstance(ds_data, dict):
            if 'Consumption' in ds_data:
                for item in ds_data['Consumption']:
                    if isinstance(item, dict):
                        pn = (item.get('ParameterKeyName') or item.get('ParameterName') or '').lower()
                        pd = (item.get('ParameterDisplayName') or '').lower()
                        if any(k in pn or k in pd for k in ['water', 'consumption']):
                            pd_list = item.get('ParameterData')
                            if isinstance(pd_list, list):
                                history_data = pd_list
                                break
            if not history_data:
                for section in ['History', 'Daily', 'ConsumptionHistory', 'WaterHistory']:
                    sec = ds_data.get(section)
                    if isinstance(sec, list):
                        for item in sec:
                            if isinstance(item, dict):
                                pn = (item.get('ParameterKeyName') or item.get('ParameterName') or '').lower()
                                if 'water' in pn:
                                    history_data = sec
                                    break
                        if history_data:
                            break
                    elif isinstance(sec, dict) and 'Water' in sec:
                        history_data = sec['Water']
                        break

    if history_data:
        if isinstance(history_data, list):
            for entry in history_data:
                if isinstance(entry, dict):
                    date_str = entry.get('Date') or entry.get('date') or entry.get('RecordDate')
                    consumption = entry.get('Consumption') or entry.get('consumption') or entry.get('Value') or entry.get('value')
                    if date_str and consumption is not None:
                        water_history.append({
                            'date': date_str,
                            'consumption_avg': float(consumption),
                        })
        elif isinstance(history_data, dict):
            for date_str, value in history_data.items():
                if value is not None:
                    water_history.append({
                        'date': date_str,
                        'consumption_avg': float(value) if isinstance(value, (int, float)) else 0,
                    })

    # CommandID 40 / dsData.Data format (primary real-world format)
    if not water_history and isinstance(response_obj.get('dsData'), dict):
        for record in response_obj['dsData'].get('Data', []):
            if not isinstance(record, dict):
                continue
            growth_day = record.get('HistoryRecord_GrowthDay')
            if growth_day is None:
                continue
            try:
                growth_day = int(growth_day)
            except (ValueError, TypeError):
                continue
            if growth_day < 0:
                continue
            raw_val = record.get('HistoryRecord_TotalDrink') or record.get('HistoryRecord_TotalWater')
            if raw_val is None:
                continue
            try:
                consumption_float = float(str(raw_val).replace(',', ''))
            except (ValueError, TypeError):
                continue
            water_history.append({
                'growth_day': growth_day,
                'date': None,
                'consumption_avg': consumption_float,
            })

    # Assign real dates
    batch_start = house.batch_start_date
    if water_history:
        if batch_start:
            for rec in water_history:
                gd = rec.get('growth_day')
                if gd is not None and gd >= 0:
                    rec['date'] = (batch_start + timedelta(days=gd)).isoformat()
        else:
            # Relative fallback: assume max growth_day = today
            valid_gds = [int(r['growth_day']) for r in water_history if r.get('growth_day') is not None and r['growth_day'] >= 0]
            if valid_gds:
                max_gd = max(valid_gds)
                today = _dt.date.today()
                for rec in water_history:
                    gd = rec.get('growth_day')
                    if gd is not None and int(gd) >= 0:
                        rec['date'] = (today - timedelta(days=(max_gd - int(gd)))).isoformat()

    # Remove records still missing a usable date
    water_history = [r for r in water_history if r.get('date') and not str(r['date']).startswith('Day ')]

    if water_history:
        water_history.sort(key=lambda x: x.get('growth_day', 0) if x.get('growth_day') is not None else x.get('date', ''))

    return water_history


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def farm_water_compare(request, farm_id):
    """
    Return water-consumption history for all active houses in one farm.

    Single Rotem login per request; results are cached in
    HouseMonitoringCache.water_history_payload (1-hour TTL).
    iOS calls this endpoint once instead of N per-house requests.

    Query params:
        days (int, 1-30, default 5): how many tail days to return per house
    """
    from houses.models import HouseMonitoringCache
    from houses.services.monitoring_cache_service import wrap_cached_response, build_meta
    from .scraper import RotemScraper

    farm = get_object_or_404(Farm, id=farm_id, is_active=True)
    days = min(max(int(request.query_params.get('days', 5)), 1), 30)
    stale_threshold_seconds = 3600  # 1 hour

    houses = list(House.objects.filter(farm=farm, is_active=True).order_by('house_number'))
    if not houses:
        return Response({'houses': {}, 'farm_id': farm_id, 'days': days})

    now = timezone.now()
    result: dict[int, list] = {}
    stale_houses = []

    # --- Fast path: serve from cache where fresh ---
    cache_by_house = {
        c.house_id: c
        for c in HouseMonitoringCache.objects.filter(house__in=houses)
    }
    for house in houses:
        cache = cache_by_house.get(house.id)
        if (
            cache
            and cache.water_history_payload
            and cache.water_history_fetched_at
            and (now - cache.water_history_fetched_at).total_seconds() < stale_threshold_seconds
        ):
            result[house.id] = cache.water_history_payload
        else:
            stale_houses.append(house)

    # --- Slow path: one Rotem login, fetch stale houses sequentially ---
    if stale_houses:
        if not farm.rotem_username or not farm.rotem_password:
            # No credentials: return whatever we have from cache
            for house in stale_houses:
                result[house.id] = cache_by_house.get(house.id, None) and cache_by_house[house.id].water_history_payload or []
        else:
            scraper = RotemScraper(username=farm.rotem_username, password=farm.rotem_password)
            if scraper.login():
                for house in stale_houses:
                    try:
                        raw = scraper.get_water_history(house_number=house.house_number) or {}
                        history = _parse_water_history_raw(raw, house)
                        result[house.id] = history
                        # Update cache
                        HouseMonitoringCache.objects.update_or_create(
                            house=house,
                            defaults={
                                'water_history_payload': history,
                                'water_history_fetched_at': now,
                            },
                        )
                    except Exception as exc:
                        logger.warning("farm_water_compare: house=%s scrape_err=%s", house.id, exc)
                        result[house.id] = cache_by_house.get(house.id, None) and cache_by_house[house.id].water_history_payload or []
            else:
                logger.error("farm_water_compare: Rotem login failed for farm=%s", farm_id)
                for house in stale_houses:
                    result[house.id] = cache_by_house.get(house.id, None) and cache_by_house[house.id].water_history_payload or []

    # Trim to requested days
    for hid, rows in result.items():
        if len(rows) > days:
            result[hid] = rows[-days:]

    return Response({
        'farm_id': farm_id,
        'days': days,
        'houses': result,
    })


def _scoped_rotem_farms(request):
    farms = Farm.objects.filter(is_active=True, integration_type='rotem')
    org_ids = user_accessible_organization_ids(request)
    if org_ids is None:
        return farms
    return farms.filter(organization_id__in=org_ids)


def get_farm_by_identifier(farm_identifier):
    """
    Resolve a farm by Rotem identifier or by internal DB id.
    This keeps endpoints working for farms that don't yet have rotem_farm_id populated.
    """
    if not farm_identifier:
        raise Farm.DoesNotExist

    farm = Farm.objects.filter(rotem_farm_id=farm_identifier).first()
    if farm:
        return farm

    if str(farm_identifier).isdigit():
        farm = Farm.objects.filter(id=int(farm_identifier)).first()
        if farm:
            return farm
        raise Farm.DoesNotExist

    raise Farm.DoesNotExist


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
        org_ids = user_accessible_organization_ids(self.request)
        if org_ids is not None:
            queryset = queryset.filter(controller__farm__organization_id__in=org_ids)
        
        # Filter by farm_id if provided (uses rotem_farm_id from Farm model)
        farm_id = self.request.query_params.get('farm_id')
        if farm_id:
            try:
                farm = get_farm_by_identifier(farm_id)
                controllers = farm.rotem_controllers.all()
                queryset = queryset.filter(controller__in=controllers)
            except Farm.DoesNotExist:
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
            farm = get_farm_by_identifier(farm_id)
            controllers = farm.rotem_controllers.all()
            data_points = self.queryset.filter(controller__in=controllers)
            serializer = self.get_serializer(data_points, many=True)
            return Response(serializer.data)
        except Farm.DoesNotExist:
            return Response({'error': 'Farm not found'}, 
                          status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get data summary by farm"""
        farms = _scoped_rotem_farms(request)
        summary = []
        
        for farm in farms:
            controllers = farm.rotem_controllers.all()
            total_points = self.queryset.filter(controller__in=controllers).count()
            recent_points = self.queryset.filter(
                controller__in=controllers,
                timestamp__gte=timezone.now() - timedelta(hours=24)
            ).count()
            
            summary.append({
                'farm_id': farm.rotem_farm_id,
                'farm_name': farm.name,
                'total_data_points': total_points,
                'recent_data_points': recent_points,
                'controllers': controllers.count()
            })
        
        return Response(summary)


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


class RotemControllerViewSet(viewsets.ReadOnlyModelViewSet):
    """API for Rotem controllers"""
    queryset = RotemController.objects.all()
    serializer_class = RotemControllerSerializer


class RotemFarmViewSet(viewsets.ReadOnlyModelViewSet):
    """API for farms with Rotem integration - now uses Farm model"""
    queryset = Farm.objects.filter(integration_type='rotem')
    serializer_class = IntegratedFarmSerializer
    lookup_field = 'rotem_farm_id'
    lookup_url_kwarg = 'farm_id'
    
    def get_queryset(self):
        """Return farms with Rotem integration"""
        return _scoped_rotem_farms(self.request).prefetch_related('rotem_controllers')


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


@api_view(['POST'])
@permission_classes([AllowAny])  # Allow external cron services to trigger
def trigger_daily_scrape(request):
    """
    API endpoint to trigger daily Rotem data collection.
    Can be called by external cron services (cron-job.org, EasyCron, etc.)
    
    Optional query parameters:
    - farm_id: Collect data for specific farm only (optional)
    
    Optional header for security:
    - X-Cron-Secret: Secret token to authenticate cron requests (if CRON_SECRET is set in settings)
    """
    from django.conf import settings
    
    # Optional secret token authentication for cron services
    cron_secret = request.headers.get('X-Cron-Secret')
    expected_secret = getattr(settings, 'CRON_SECRET', None)
    
    if expected_secret and cron_secret != expected_secret:
        return Response(
            {'error': 'Invalid or missing cron secret token'}, 
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    farm_id = request.data.get('farm_id') or request.query_params.get('farm_id')
    
    try:
        service = DjangoRotemScraperService(farm_id=farm_id if farm_id else None)
        
        if farm_id:
            # Scrape specific farm
            scrape_log = service.scrape_and_save_data()
            
            return Response({
                'status': 'success',
                'message': f'Data collection completed for farm {farm_id}',
                'scrape_status': scrape_log.status,
                'data_points_collected': scrape_log.data_points_collected,
                'completed_at': scrape_log.completed_at.isoformat() if scrape_log.completed_at else None,
                'error_message': scrape_log.error_message if scrape_log.status != 'success' else None
            })
        else:
            # Scrape all farms
            results = service.scrape_all_farms()
            successful_farms = [r for r in results if r.get('status') == 'success']
            total_data_points = sum(r.get('data_points_collected', 0) for r in results)
            
            return Response({
                'status': 'success',
                'message': f'Data collection completed for {len(successful_farms)} farms',
                'total_farms': len(results),
                'successful_farms': len(successful_farms),
                'total_data_points_collected': total_data_points,
                'results': results
            })
    except Exception as e:
        return Response(
            {'status': 'error', 'error': f'Failed to collect Rotem data: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class RotemDailySummaryViewSet(viewsets.ReadOnlyModelViewSet):
    """API for daily aggregated Rotem data summaries"""
    queryset = RotemDailySummary.objects.all()
    serializer_class = RotemDailySummarySerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['controller', 'date']
    search_fields = ['controller__controller_name', 'controller__farm__name']
    ordering_fields = ['date', 'total_data_points']
    ordering = ['-date']
    
    def get_queryset(self):
        """Filter queryset based on query parameters"""
        queryset = super().get_queryset()
        org_ids = user_accessible_organization_ids(self.request)
        if org_ids is not None:
            queryset = queryset.filter(controller__farm__organization_id__in=org_ids)
        
        # Filter by farm_id if provided (uses rotem_farm_id from Farm model)
        farm_id = self.request.query_params.get('farm_id')
        if farm_id:
            try:
                farm = get_farm_by_identifier(farm_id)
                controllers = farm.rotem_controllers.all()
                queryset = queryset.filter(controller__in=controllers)
            except Farm.DoesNotExist:
                queryset = queryset.none()
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        
        # Filter by controller_id if provided
        controller_id = self.request.query_params.get('controller_id')
        if controller_id:
            queryset = queryset.filter(controller_id=controller_id)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def by_farm(self, request):
        """Get daily summaries for a specific farm"""
        farm_id = request.query_params.get('farm_id')
        if not farm_id:
            return Response(
                {'error': 'farm_id parameter is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            farm = get_farm_by_identifier(farm_id)
            controllers = farm.rotem_controllers.all()
            summaries = RotemDailySummary.objects.filter(
                controller__in=controllers
            ).order_by('-date')
            
            serializer = self.get_serializer(summaries, many=True)
            return Response(serializer.data)
        except Farm.DoesNotExist:
            return Response(
                {'error': 'Farm not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['get'])
    def by_controller(self, request):
        """Get daily summaries for a specific controller"""
        controller_id = request.query_params.get('controller_id')
        if not controller_id:
            return Response(
                {'error': 'controller_id parameter is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        summaries = RotemDailySummary.objects.filter(
            controller_id=controller_id
        ).order_by('-date')
        
        serializer = self.get_serializer(summaries, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Get recent daily summaries (last 30 days)"""
        days = int(request.query_params.get('days', 30))
        cutoff_date = timezone.now().date() - timedelta(days=days)
        
        summaries = RotemDailySummary.objects.filter(
            date__gte=cutoff_date
        ).order_by('-date')
        
        serializer = self.get_serializer(summaries, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='water-history')
    def water_history(self, request):
        """Get water consumption history for a specific house.

        Cache-first: serves HouseMonitoringCache.water_history_payload when
        fresh (< 1 hour old), avoiding a live Rotem login for every request.
        Falls back to a live CommandID 40 scrape only when the cache is cold.
        """
        from .scraper import RotemScraper
        from .services.scraper_service import DjangoRotemScraperService
        from houses.models import HouseMonitoringCache
        import json

        house_id = request.query_params.get('house_id')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        days = request.query_params.get('days')

        if not house_id:
            return Response(
                {'error': 'house_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # --- Cache-first shortcut ---
        try:
            _house = House.objects.get(pk=house_id)
            cache = HouseMonitoringCache.objects.filter(house=_house).first()
            stale_threshold = 3600  # 1 hour
            if (
                cache
                and cache.water_history_payload
                and cache.water_history_fetched_at
                and (timezone.now() - cache.water_history_fetched_at).total_seconds() < stale_threshold
            ):
                days_param = min(max(int(days or 5), 1), 30) if days else 5
                history = list(cache.water_history_payload)
                if len(history) > days_param:
                    history = history[-days_param:]
                return Response({
                    'house_id': int(house_id),
                    'house_number': _house.house_number,
                    'farm_name': _house.farm.name if _house.farm else None,
                    'water_history': history,
                    'total_days': len(history),
                    'average_consumption': sum(h.get('consumption_avg', 0) for h in history) / len(history) if history else 0,
                    'source': 'cache',
                })
        except House.DoesNotExist:
            return Response({'error': 'House not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception:
            pass  # Cache miss — fall through to live scrape
        
        try:
            house = House.objects.get(pk=house_id)
            
            # Get the farm and check if it's integrated with Rotem
            # Use permissive check: allow if integration_type is 'rotem' or if rotem_farm_id exists
            if not house.farm:
                return Response(
                    {'error': 'House is not connected to a farm'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check if farm is integrated with Rotem
            is_rotem_integrated = (
                house.farm.integration_type == 'rotem' or
                (house.farm.rotem_farm_id and house.farm.rotem_farm_id.strip() != '') or
                house.farm.is_integrated
            )
            
            if not is_rotem_integrated:
                return Response(
                    {'error': 'House is not connected to a Rotem-integrated farm'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check if farm has Rotem credentials
            if not house.farm.rotem_username or not house.farm.rotem_password:
                return Response(
                    {'error': 'Farm Rotem credentials are not configured. Please configure Rotem integration settings for this farm.'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get rotem_farm_id for logging (use farm database ID as fallback if not set)
            rotem_farm_id = house.farm.rotem_farm_id
            if not rotem_farm_id or rotem_farm_id.strip() == '':
                # Use farm database ID as fallback for logging/reference
                rotem_farm_id = str(house.farm.id)
                logger.warning(f"rotem_farm_id not set for farm {house.farm.id}, using farm ID as reference: {rotem_farm_id}")
            
            # Initialize Rotem scraper with farm credentials directly
            try:
                scraper = RotemScraper(
                    username=house.farm.rotem_username,
                    password=house.farm.rotem_password
                )
                
                # Login to Rotem
                if not scraper.login():
                    return Response(
                        {'error': 'Failed to authenticate with Rotem API'}, 
                        status=status.HTTP_401_UNAUTHORIZED
                    )
                
                # Select the farm if farm_connection_token is available
                # The farm_connection_token should be set during login, but we may need to select the farm
                if rotem_farm_id and scraper.farm_connection_token:
                    logger.info(f"  Farm connection token available: {scraper.farm_connection_token[:20]}...")
                
                logger.info(f"Water History API Call - House ID: {house_id}, House Number: {house.house_number}")
                logger.info(f"  Farm Rotem ID: {rotem_farm_id}")
                logger.info(f"  Fetching from Rotem API directly...")
                
                # Fetch water history from Rotem API
                raw_water_data = scraper.get_water_history(
                    house_number=house.house_number,
                    start_date=start_date,
                    end_date=end_date
                )
                
                # Log the raw response from Rotem API
                logger.info(f"  Raw Rotem API response: {json.dumps(raw_water_data, indent=2, default=str)[:5000]}")
                
                # Log dsData structure if available
                if isinstance(raw_water_data, dict) and 'reponseObj' in raw_water_data:
                    response_obj = raw_water_data['reponseObj']
                    if 'dsData' in response_obj:
                        ds_data = response_obj['dsData']
                        logger.info(f"  dsData structure: {json.dumps(ds_data, indent=2, default=str)[:3000]}")
                        if isinstance(ds_data, dict):
                            logger.info(f"  dsData keys: {list(ds_data.keys())}")
                            for key in ds_data.keys():
                                if isinstance(ds_data[key], list):
                                    logger.info(f"    {key}: array with {len(ds_data[key])} items")
                                elif isinstance(ds_data[key], dict):
                                    logger.info(f"    {key}: dict with keys {list(ds_data[key].keys())}")
                
                if not raw_water_data:
                    return Response({
                        'house_id': int(house_id),
                        'house_number': house.house_number,
                        'farm_name': house.farm.name if house.farm else None,
                        'water_history': [],
                        'total_days': 0,
                        'average_consumption': 0,
                        'message': 'No water history data available from Rotem API',
                    })
                
                # Parse the Rotem API response
                # The structure may vary, so we need to handle different response formats
                water_history = []
                
                # Try to extract water history from different possible response structures
                response_obj = raw_water_data.get('reponseObj', raw_water_data)
                
                # Check various possible locations for water history data
                history_data = None
                if 'WaterHistory' in response_obj:
                    history_data = response_obj['WaterHistory']
                elif 'ConsumptionHistory' in response_obj:
                    history_data = response_obj['ConsumptionHistory']
                elif isinstance(response_obj.get('History'), dict) and 'Water' in response_obj['History']:
                    history_data = response_obj['History']['Water']
                elif 'dsData' in response_obj:
                    # Check if dsData contains consumption data
                    ds_data = response_obj['dsData']
                    logger.info(f"  dsData keys: {list(ds_data.keys()) if isinstance(ds_data, dict) else 'Not a dict'}")
                    
                    # Look for Consumption array in dsData
                    if 'Consumption' in ds_data:
                        consumption = ds_data['Consumption']
                        logger.info(f"  Found Consumption array with {len(consumption) if isinstance(consumption, list) else 'non-list'} items")
                        
                        # Look for water-related parameters in consumption array
                        water_params = []
                        for item in consumption:
                            if isinstance(item, dict):
                                param_name = item.get('ParameterKeyName', '') or item.get('ParameterName', '')
                                param_display = item.get('ParameterDisplayName', '')
                                # Check if this is a water-related parameter
                                if any(keyword in param_name.lower() or keyword in param_display.lower() 
                                       for keyword in ['water', 'consumption', 'daily_water', 'water_consumption']):
                                    water_params.append(item)
                                    logger.info(f"    Found water parameter: {param_name} = {item.get('ParameterValue')}")
                        
                        if water_params:
                            # If we found water parameters, check if they have historical data
                            # The ParameterData field might contain historical values
                            for param in water_params:
                                param_data = param.get('ParameterData')
                                if param_data:
                                    logger.info(f"    Parameter {param.get('ParameterKeyName')} has ParameterData: {type(param_data)}")
                                    # ParameterData might be a list of historical values
                                    if isinstance(param_data, list):
                                        history_data = param_data
                                        break
                    
                    # Also check other sections like "History", "Daily", etc.
                    for section_name in ['History', 'Daily', 'ConsumptionHistory', 'WaterHistory']:
                        if section_name in ds_data:
                            section_data = ds_data[section_name]
                            logger.info(f"  Found {section_name} section in dsData")
                            if isinstance(section_data, list):
                                # Look for water-related items
                                for item in section_data:
                                    if isinstance(item, dict):
                                        param_name = item.get('ParameterKeyName', '') or item.get('ParameterName', '')
                                        if 'water' in param_name.lower():
                                            history_data = section_data
                                            break
                            elif isinstance(section_data, dict):
                                if 'Water' in section_data:
                                    history_data = section_data['Water']
                                    break
                
                # If we found history data, parse it
                if history_data:
                    logger.info(f"  Found history data structure: {type(history_data)}")
                    if isinstance(history_data, list):
                        for entry in history_data:
                            if isinstance(entry, dict):
                                # Parse entry based on Rotem API structure
                                date_str = entry.get('Date') or entry.get('date') or entry.get('RecordDate')
                                consumption = entry.get('Consumption') or entry.get('consumption') or entry.get('Value') or entry.get('value')
                                
                                if date_str and consumption is not None:
                                    water_history.append({
                                        'date': date_str,
                                        'consumption_avg': float(consumption),
                                        'consumption_min': entry.get('Min', consumption),
                                        'consumption_max': entry.get('Max', consumption),
                                        'data_points': entry.get('Count', 1),
                                    })
                    elif isinstance(history_data, dict):
                        # Handle dictionary format
                        for date_str, value in history_data.items():
                            if value is not None:
                                water_history.append({
                                    'date': date_str,
                                    'consumption_avg': float(value) if isinstance(value, (int, float)) else 0,
                                    'consumption_min': float(value) if isinstance(value, (int, float)) else 0,
                                    'consumption_max': float(value) if isinstance(value, (int, float)) else 0,
                                    'data_points': 1,
                                })
                
                # Check dsData.Data array for water history records (CommandID 40 format)
                if not water_history and 'dsData' in response_obj:
                    ds_data = response_obj['dsData']
                    if 'Data' in ds_data and isinstance(ds_data['Data'], list):
                        logger.info(f"  Found dsData.Data array with {len(ds_data['Data'])} records")
                        
                        # Parse water history records from Data array
                        for record in ds_data['Data']:
                            if isinstance(record, dict):
                                # Extract growth day (this represents the day number)
                                growth_day = record.get('HistoryRecord_GrowthDay')
                                if growth_day is None or growth_day < 0:
                                    continue  # Skip invalid or summary rows (growth_day -1 is summary)
                                
                                # Extract total water consumption
                                total_drink = record.get('HistoryRecord_TotalDrink')
                                total_water = record.get('HistoryRecord_TotalWater')
                                
                                # Use TotalDrink as primary value, fallback to TotalWater
                                consumption_value = total_drink or total_water
                                
                                if consumption_value:
                                    try:
                                        # Convert to float, handling string values
                                        consumption_float = float(str(consumption_value).replace(',', ''))
                                        
                                        # Calculate date based on growth day and house start date
                                        # The actual date should be calculated from house.batch_start_date + growth_day
                                        # For now, we'll use growth_day as a relative day indicator
                                        water_history.append({
                                            'date': f"Day {int(growth_day)}",  # Will be converted to actual date later
                                            'growth_day': int(growth_day),
                                            'consumption_avg': consumption_float,
                                            'consumption_min': consumption_float,
                                            'consumption_max': consumption_float,
                                            'data_points': 1,
                                            'total_drink': consumption_float,
                                            'daily_water_1': float(str(record.get('HistoryRecord_DailyWater_1', '0')).replace(',', '')) or 0,
                                            'daily_water_2': float(str(record.get('HistoryRecord_DailyWater_2', '0')).replace(',', '')) or 0,
                                            'daily_water_3': float(str(record.get('HistoryRecord_DailyWater_3', '0')).replace(',', '')) or 0,
                                            'daily_water_4': float(str(record.get('HistoryRecord_DailyWater_4', '0')).replace(',', '')) or 0,
                                            'cooling': float(str(record.get('HistoryRecord_Cooling', '0')).replace(',', '')) or 0,
                                            'fogger': float(str(record.get('HistoryRecord_Fogger', '0')).replace(',', '')) or 0,
                                        })
                                    except (ValueError, TypeError) as e:
                                        logger.warning(f"    Could not parse consumption value for day {growth_day}: {e}")
                                        continue
                        
                        logger.info(f"  Parsed {len(water_history)} water history records from dsData.Data")
                
                # If no structured history found, log the full response for debugging
                if not water_history:
                    logger.warning(f"  Could not parse water history from Rotem API response structure")
                    logger.warning(f"  Full response keys: {list(raw_water_data.keys()) if isinstance(raw_water_data, dict) else 'Not a dict'}")
                    if isinstance(raw_water_data, dict) and 'reponseObj' in raw_water_data:
                        logger.warning(f"  reponseObj keys: {list(raw_water_data['reponseObj'].keys())}")
                
                logger.info(f"  Parsed water history records: {len(water_history)}")
                
                # Convert growth_day to actual dates based on house start date
                if water_history and house.batch_start_date:
                    from datetime import timedelta
                    for record in water_history:
                        if 'growth_day' in record and record['growth_day'] >= 0:
                            actual_date = house.batch_start_date + timedelta(days=int(record['growth_day']))
                            record['date'] = actual_date.isoformat()
                elif water_history:
                    # No batch_start_date: derive relative dates so iOS can chart them.
                    # Assume the highest growth_day corresponds to today.
                    import datetime as _dt
                    valid_gds = [int(r['growth_day']) for r in water_history if 'growth_day' in r and r['growth_day'] >= 0]
                    if valid_gds:
                        max_gd = max(valid_gds)
                        today = _dt.date.today()
                        for record in water_history:
                            gd = record.get('growth_day')
                            if gd is not None and int(gd) >= 0:
                                record['date'] = (today - timedelta(days=(max_gd - int(gd)))).isoformat()
                
                # Sort by growth_day or date
                if water_history:
                    if 'growth_day' in water_history[0]:
                        water_history.sort(key=lambda x: x.get('growth_day', 0))
                    else:
                        water_history.sort(key=lambda x: x.get('date', ''))
                
                # Persist to cache so subsequent per-house requests are instant
                if water_history:
                    from houses.models import HouseMonitoringCache
                    try:
                        HouseMonitoringCache.objects.update_or_create(
                            house=house,
                            defaults={
                                'water_history_payload': water_history,
                                'water_history_fetched_at': timezone.now(),
                            },
                        )
                    except Exception as _ce:
                        logger.warning("water_history cache write failed house=%s err=%s", house_id, _ce)

                return Response({
                    'house_id': int(house_id),
                    'house_number': house.house_number,
                    'farm_name': house.farm.name if house.farm else None,
                    'water_history': water_history,
                    'total_days': len(water_history),
                    'average_consumption': sum(h['consumption_avg'] for h in water_history) / len(water_history) if water_history else 0,
                    'source': 'live',
                })
                
            except Exception as e:
                logger.error(f"Error fetching water history from Rotem API: {str(e)}", exc_info=True)
                return Response(
                    {'error': f'Failed to fetch water history from Rotem API: {str(e)}'}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                
        except House.DoesNotExist:
            return Response(
                {'error': 'House not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error in water_history endpoint: {str(e)}", exc_info=True)
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'], url_path='temperature-history')
    def temperature_history(self, request):
        """Get temperature history for a specific house using CommandID 35."""
        house_id = request.query_params.get('house_id')
        if not house_id:
            return Response({'error': 'house_id parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            house = House.objects.get(pk=house_id)
            rows, err = _rotem_history_command_payload(house, command_id="35")
            if err:
                return Response({'error': err}, status=status.HTTP_401_UNAUTHORIZED)
            history = []
            for row in rows or []:
                if not isinstance(row, dict):
                    continue
                growth_day = row.get('QueueRecord_GrowthDay') or row.get('HistoryRecord_GrowthDay')
                if growth_day is None:
                    continue
                try:
                    growth_day = int(growth_day)
                except (ValueError, TypeError):
                    continue
                if growth_day < 0:
                    continue
                history.append({
                    'growth_day': growth_day,
                    'min_value': _safe_float(row.get('QueueRecord_MinimumValue')),
                    'avg_value': _safe_float(row.get('QueueRecord_AverageValue')),
                    'max_value': _safe_float(row.get('QueueRecord_MaximumValue')),
                    'date': (house.batch_start_date + timedelta(days=growth_day)).isoformat() if house.batch_start_date else None,
                })
            history.sort(key=lambda x: x['growth_day'])
            return Response({
                'house_id': int(house_id),
                'house_number': house.house_number,
                'temperature_history': history,
                'total_days': len(history),
            })
        except House.DoesNotExist:
            return Response({'error': 'House not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error("temperature_history failed: %s", e, exc_info=True)
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'], url_path='feed-history')
    def feed_history(self, request):
        """Get feed history for a specific house using CommandID 41."""
        house_id = request.query_params.get('house_id')
        if not house_id:
            return Response({'error': 'house_id parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            house = House.objects.get(pk=house_id)
            rows, err = _rotem_history_command_payload(house, command_id="41")
            if err:
                return Response({'error': err}, status=status.HTTP_401_UNAUTHORIZED)
            history = []
            for row in rows or []:
                if not isinstance(row, dict):
                    continue
                growth_day = row.get('HistoryRecord_GrowthDay')
                if growth_day is None:
                    continue
                try:
                    growth_day = int(growth_day)
                except (ValueError, TypeError):
                    continue
                if growth_day < 0:
                    continue
                history.append({
                    'growth_day': growth_day,
                    'daily_feed_total': _safe_float(
                        row.get('HistoryRecord_DailyFeed')
                        or row.get('HistoryRecord_TotalFeed')
                        or row.get('DailyFeed')
                    ),
                    'change_percent': _safe_float(row.get('HistoryRecord_ChangeFeed')),
                    'feed_per_bird': _safe_float(row.get('HistoryRecord_FeedPerBird')),
                    'date': (house.batch_start_date + timedelta(days=growth_day)).isoformat() if house.batch_start_date else None,
                })
            history.sort(key=lambda x: x['growth_day'])
            # Derive relative dates when batch_start_date is absent.
            if history and not house.batch_start_date:
                import datetime as _dt
                max_gd = history[-1]['growth_day']
                today = _dt.date.today()
                for rec in history:
                    rec['date'] = (today - timedelta(days=(max_gd - rec['growth_day']))).isoformat()
            return Response({
                'house_id': int(house_id),
                'house_number': house.house_number,
                'feed_history': history,
                'total_days': len(history),
            })
        except House.DoesNotExist:
            return Response({'error': 'House not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error("feed_history failed: %s", e, exc_info=True)
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
