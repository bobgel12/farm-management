from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q, Avg, Max, Min
from django.utils import timezone
from datetime import timedelta, datetime, date
from .models import (
    House,
    HouseMonitoringSnapshot,
    HouseAlarm,
    Device,
    DeviceStatus,
    ControlSettings,
    TemperatureCurve,
    HouseConfiguration,
    Sensor,
    WaterConsumptionAlert,
    WaterConsumptionForecast,
)
from .serializers import (
    HouseSerializer, HouseListSerializer,
    HouseMonitoringSnapshotSerializer, HouseMonitoringSummarySerializer,
    HouseMonitoringStatsSerializer, HouseAlarmSerializer,
    HouseComparisonSerializer, DeviceSerializer, DeviceStatusSerializer,
    ControlSettingsSerializer, TemperatureCurveSerializer,
    HouseConfigurationSerializer, SensorSerializer,
    WaterConsumptionAlertSerializer, WaterConsumptionForecastSerializer,
)
from farms.models import Farm
from farms.serializers import FlockSerializer
from farms.services.rotem_flock_sync import upsert_active_flock_from_rotem
from tasks.task_scheduler import TaskScheduler
from tasks.serializers import TaskSerializer
from collections import defaultdict
from .services.water_forecast_service import WaterForecastService
from .services.monitoring_contract import MonitoringUnits
from .services.heater_history_payload import build_heater_history_payload
from .services.monitoring_cache_service import (
    MAX_STALE_SECONDS,
    build_meta,
    upsert_farm_monitoring_cache,
    wrap_cached_response,
)
from .models import FarmMonitoringCache, HouseMonitoringCache
from rotem_scraper.tasks import sync_refresh_house_heater_history
from farms.views import user_accessible_organization_ids
from rotem_scraper.scraper import RotemScraper


def _cache_mode(request):
    mode = (request.query_params.get('mode') or 'cached_then_live').lower()
    if mode not in ('cached', 'live', 'cached_then_live'):
        return 'cached'
    return mode


def _should_refresh(meta: dict):
    return bool(meta.get('is_stale')) and meta.get('refresh_state') != 'refreshing'


def _house_from_scope_or_404(request, house_id: int) -> House:
    return get_object_or_404(_scoped_houses_queryset(request), id=house_id)


def _house_rotem_scraper_or_error(house: House):
    farm = house.farm
    is_rotem_integrated = (
        farm.integration_type == 'rotem' or
        (farm.rotem_farm_id and str(farm.rotem_farm_id).strip() != '') or
        farm.is_integrated
    )
    if not is_rotem_integrated:
        return None, Response(
            {'detail': 'House farm is not Rotem-integrated.'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if not farm.rotem_username or not farm.rotem_password:
        return None, Response(
            {'detail': 'Farm Rotem credentials are not configured.'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    scraper = RotemScraper(username=farm.rotem_username, password=farm.rotem_password)
    if not scraper.login():
        return None, Response(
            {'detail': 'Failed to authenticate with Rotem API.'},
            status=status.HTTP_502_BAD_GATEWAY,
        )
    return scraper, None


def _safe_float(value):
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _extract_current_numeric(house_data: dict, key: str):
    section = house_data.get(key, {}) if isinstance(house_data, dict) else {}
    if not isinstance(section, dict):
        return None
    return _safe_float(section.get('CurrentNumericValue'))


def _extract_live_house_from_site_controllers(payload: dict, house_number: int):
    response_obj = payload.get('reponseObj') if isinstance(payload, dict) else None
    farm_houses = response_obj.get('FarmHouses', []) if isinstance(response_obj, dict) else []
    target = None
    for row in farm_houses:
        if isinstance(row, dict) and int(row.get('HouseNumber', -1)) == int(house_number):
            target = row
            break
    if not target:
        return None

    data = target.get('Data', {}) if isinstance(target.get('Data'), dict) else {}
    # Rotem "GetSiteControllersInfo" provides direct daily values in this bundle.
    average_temperature = _extract_current_numeric(data, 'Temperature')
    humidity = _extract_current_numeric(data, 'Humidity')
    static_pressure = _extract_current_numeric(data, 'Pressure')
    airflow_percentage = _extract_current_numeric(data, 'VentLevel')
    water_consumption = _extract_current_numeric(data, 'DailyWater')
    feed_consumption = _extract_current_numeric(data, 'DailyFeed')

    last_update = response_obj.get('LastUpdateDT') if isinstance(response_obj, dict) else None
    timestamp = timezone.now()
    if isinstance(last_update, str):
        try:
            timestamp = datetime.fromisoformat(last_update.replace('Z', '+00:00'))
        except ValueError:
            timestamp = timezone.now()

    return {
        'house_id': int(target.get('HouseNumber', house_number)),
        'source_timestamp': timestamp.isoformat(),
        'timestamp': timezone.now().isoformat(),
        'average_temperature': average_temperature,
        'humidity': humidity,
        'static_pressure': static_pressure,
        'airflow_percentage': airflow_percentage,
        'water_consumption': water_consumption,
        'feed_consumption': feed_consumption,
        'is_connected': int(target.get('ConnectionStatus', 0)) == 1,
        'alarm_status': 'normal',
    }


def _extract_comparison_item(response_obj: dict, category: str, house_number: int):
    if not isinstance(response_obj, dict):
        return None
    dic = response_obj.get('DicComparisonItems', {})
    if not isinstance(dic, dict):
        return None
    bucket = dic.get(category, {})
    if not isinstance(bucket, dict):
        return None
    return bucket.get(f'House{house_number}')


def _scoped_farms_queryset(request):
    farms = Farm.objects.all()
    org_ids = user_accessible_organization_ids(request)
    if org_ids is None:
        return farms
    return farms.filter(organization_id__in=org_ids)


def _scoped_houses_queryset(request):
    houses = House.objects.select_related('farm')
    org_ids = user_accessible_organization_ids(request)
    if org_ids is None:
        return houses
    return houses.filter(farm__organization_id__in=org_ids)


def _scoped_water_alerts_queryset(request):
    alerts = WaterConsumptionAlert.objects.select_related('house', 'house__farm')
    org_ids = user_accessible_organization_ids(request)
    if org_ids is None:
        return alerts
    return alerts.filter(house__farm__organization_id__in=org_ids)


class HouseListCreateView(generics.ListCreateAPIView):
    serializer_class = HouseSerializer

    def get_queryset(self):
        farm_id = self.request.query_params.get('farm_id')
        queryset = _scoped_houses_queryset(self.request)
        if farm_id:
            return queryset.filter(farm_id=farm_id)
        return queryset

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return HouseListSerializer
        return HouseSerializer

    def perform_create(self, serializer):
        house = serializer.save()
        # Automatically generate tasks for the new house
        TaskScheduler.generate_tasks_for_house(house)
        
        # Auto-complete past tasks if the house has a chicken_in_date in the past
        if house.chicken_in_date:
            current_day = house.current_day
            if current_day is not None and current_day > 0:
                from tasks.models import Task
                from django.utils import timezone
                
                past_tasks = Task.objects.filter(
                    house=house,
                    day_offset__lt=current_day,
                    is_completed=False
                )
                
                if past_tasks.exists():
                    past_tasks.update(
                        is_completed=True,
                        completed_at=timezone.now(),
                        completed_by='system_auto_complete',
                        notes='Automatically marked as completed - past task after house creation'
                    )
        
        return house


class HouseDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = House.objects.all()
    serializer_class = HouseSerializer


@api_view(['GET'])
def house_dashboard(request):
    """Get dashboard data for all houses"""
    houses = House.objects.filter(is_active=True)
    
    # Count houses by status
    status_counts = {}
    for house in houses:
        status = house.status
        status_counts[status] = status_counts.get(status, 0) + 1
    
    # Get houses that need attention today
    today_houses = []
    for house in houses:
        current_day = house.current_day
        if current_day is not None and current_day in [-1, 0, 1, 7, 8, 13, 14, 20, 21, 35, 39, 40, 41]:
            today_houses.append({
                'id': house.id,
                'farm_name': house.farm.name,
                'house_number': house.house_number,
                'current_day': current_day,
                'status': house.status
            })
    
    data = {
        'total_houses': houses.count(),
        'status_counts': status_counts,
        'today_houses': today_houses
    }
    return Response(data)


@api_view(['GET'])
def farm_houses(request, farm_id):
    """Get all houses for a specific farm"""
    farm = get_object_or_404(_scoped_farms_queryset(request), id=farm_id)
    houses = House.objects.filter(farm=farm)
    serializer = HouseListSerializer(houses, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def farm_house_detail(request, farm_id, house_id):
    """Get a specific house within a farm context"""
    farm = get_object_or_404(_scoped_farms_queryset(request), id=farm_id)
    house = get_object_or_404(House, id=house_id, farm=farm)
    serializer = HouseSerializer(house)
    return Response(serializer.data)


@api_view(['GET'])
def farm_task_summary(request, farm_id):
    """Get task summary for all houses in a farm"""
    farm = get_object_or_404(Farm, id=farm_id)
    houses = House.objects.filter(farm=farm, is_active=True)
    
    summary = {
        'farm_name': farm.name,
        'total_houses': houses.count(),
        'houses': []
    }
    
    for house in houses:
        current_day = house.current_day
        house_data = {
            'id': house.id,
            'house_number': house.house_number,
            'current_day': current_day,
            'status': house.status,
            'chicken_in_date': house.chicken_in_date,
            'chicken_out_date': house.chicken_out_date,
            'tasks': {
                'total': 0,
                'completed': 0,
                'pending': 0,
                'overdue': 0,
                'today': 0
            },
            'pending_tasks': []
        }
        
        if current_day is not None:
            from tasks.models import Task
            
            # Get all tasks for this house
            all_tasks = Task.objects.filter(house=house)
            house_data['tasks']['total'] = all_tasks.count()
            house_data['tasks']['completed'] = all_tasks.filter(is_completed=True).count()
            house_data['tasks']['pending'] = all_tasks.filter(is_completed=False).count()
            
            # Get today's tasks
            today_tasks = all_tasks.filter(day_offset=current_day, is_completed=False)
            house_data['tasks']['today'] = today_tasks.count()
            
            # Get overdue tasks (tasks from previous days that are incomplete)
            if current_day > 0:
                overdue_tasks = all_tasks.filter(
                    day_offset__lt=current_day,
                    is_completed=False
                )
                house_data['tasks']['overdue'] = overdue_tasks.count()
            
            # Get pending tasks (future tasks and today's tasks)
            pending_tasks = all_tasks.filter(
                day_offset__gte=current_day,
                is_completed=False
            ).order_by('day_offset', 'task_name')
            
            house_data['pending_tasks'] = [
                {
                    'id': task.id,
                    'task_name': task.task_name,
                    'description': task.description,
                    'day_offset': task.day_offset,
                    'task_type': task.task_type,
                    'is_today': task.day_offset == current_day
                }
                for task in pending_tasks
            ]
        
        summary['houses'].append(house_data)
    
    return Response(summary)


# Monitoring endpoints

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def house_monitoring_latest(request, house_id):
    """Get latest monitoring data (cached-first by default, live optional)."""
    house = _house_from_scope_or_404(request, house_id)
    mode = _cache_mode(request)
    cache = HouseMonitoringCache.objects.filter(house=house).first()
    if mode != 'live' and cache and cache.latest_payload:
        meta = build_meta(
            fetched_at=cache.fetched_at,
            source_timestamp=cache.source_timestamp,
            refresh_state=cache.refresh_state,
            stale_seconds=MAX_STALE_SECONDS,
        )
        if mode == 'cached_then_live' and _should_refresh(meta):
            upsert_farm_monitoring_cache(house.farm)
            cache.refresh_from_db()
            meta = build_meta(
                fetched_at=cache.fetched_at,
                source_timestamp=cache.source_timestamp,
                refresh_state=cache.refresh_state,
                stale_seconds=MAX_STALE_SECONDS,
            )
        return Response(wrap_cached_response(cache.latest_payload, meta))

    scraper, err = _house_rotem_scraper_or_error(house)
    if err:
        return err

    site_payload = scraper.get_site_controllers_info()
    if not site_payload:
        return Response(
            {'detail': 'No live data returned from Rotem.'},
            status=status.HTTP_502_BAD_GATEWAY,
        )
    live = _extract_live_house_from_site_controllers(site_payload, house.house_number)
    if not live:
        return Response(
            {'detail': 'House live data not found in Rotem response.'},
            status=status.HTTP_404_NOT_FOUND,
        )
    HouseMonitoringCache.objects.update_or_create(
        house=house,
        defaults={
            'latest_payload': live,
            'source_timestamp': datetime.fromisoformat(live['source_timestamp'].replace('Z', '+00:00')),
            'refresh_state': 'fresh',
            'last_error': '',
        },
    )
    cache = HouseMonitoringCache.objects.filter(house=house).first()
    meta = build_meta(
        fetched_at=cache.fetched_at if cache else timezone.now(),
        source_timestamp=cache.source_timestamp if cache else timezone.now(),
        refresh_state='fresh',
        stale_seconds=MAX_STALE_SECONDS,
    )
    return Response(wrap_cached_response(live, meta))


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def house_monitoring_history(request, house_id):
    """Get house monitoring history (cached-first by default)."""
    house = _house_from_scope_or_404(request, house_id)
    mode = _cache_mode(request)
    cache = HouseMonitoringCache.objects.filter(house=house).first()
    if mode != 'live' and cache and cache.history_payload:
        meta = build_meta(cache.fetched_at, cache.source_timestamp, cache.refresh_state, MAX_STALE_SECONDS)
        if mode == 'cached_then_live' and _should_refresh(meta):
            upsert_farm_monitoring_cache(house.farm)
            cache.refresh_from_db()
            meta = build_meta(cache.fetched_at, cache.source_timestamp, cache.refresh_state, MAX_STALE_SECONDS)
        return Response(wrap_cached_response(cache.history_payload, meta))

    scraper, err = _house_rotem_scraper_or_error(house)
    if err:
        return err

    # Keep existing query contract.
    start_date = request.query_params.get('start_date')
    end_date = request.query_params.get('end_date')
    limit = int(request.query_params.get('limit', 100))
    end_dt = timezone.now()
    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            end_dt = timezone.now()
    start_dt = end_dt - timedelta(days=5)
    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            pass

    raw_water = scraper.get_water_history(
        house_number=house.house_number,
        start_date=start_dt.date().isoformat(),
        end_date=end_dt.date().isoformat(),
    ) or {}
    response_obj = raw_water.get('reponseObj', raw_water) if isinstance(raw_water, dict) else {}
    ds_data = response_obj.get('dsData', {}) if isinstance(response_obj, dict) else {}
    rows = ds_data.get('Data', []) if isinstance(ds_data, dict) else []

    results = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        growth_day = row.get('HistoryRecord_GrowthDay') or row.get('HistoryRecord_Heaters_GrowthDay')
        date_str = row.get('HistoryRecord_Date')
        ts = None
        if isinstance(date_str, str):
            try:
                ts = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            except ValueError:
                ts = None
        if ts is None and growth_day is not None and house.batch_start_date:
            try:
                ts = datetime.combine(house.batch_start_date + timedelta(days=int(growth_day)), datetime.min.time(), tzinfo=timezone.get_current_timezone())
            except (TypeError, ValueError):
                ts = timezone.now()
        if ts is None:
            ts = timezone.now()

        water = _safe_float(row.get('HistoryRecord_DailyWater') or row.get('DailyWater') or row.get('Water'))
        feed = _safe_float(row.get('HistoryRecord_DailyFeed') or row.get('DailyFeed') or row.get('Feed'))
        results.append({
            'source_timestamp': ts.isoformat(),
            'timestamp': timezone.now().isoformat(),
            'average_temperature': None,
            'humidity': None,
            'static_pressure': None,
            'airflow_percentage': None,
            'water_consumption': water,
            'feed_consumption': feed,
        })

    # Add latest live general sample so clients still get realtime environment fields.
    site_payload = scraper.get_site_controllers_info()
    live = _extract_live_house_from_site_controllers(site_payload or {}, house.house_number)
    if live:
        results.append(live)

    results = sorted(results, key=lambda x: x.get('source_timestamp') or x.get('timestamp'))[-limit:]
    payload = {
        'count': len(results),
        'start_date': start_dt.isoformat(),
        'end_date': end_dt.isoformat(),
        'contract': {
            'timestamp_fields': {
                'source': 'source_timestamp',
                'ingested': 'timestamp',
            },
            'units': MonitoringUnits().__dict__,
        },
        'results': results
    }
    HouseMonitoringCache.objects.update_or_create(
        house=house,
        defaults={
            'history_payload': payload,
            'source_timestamp': timezone.now(),
            'refresh_state': 'fresh',
            'last_error': '',
        },
    )
    cache = HouseMonitoringCache.objects.filter(house=house).first()
    meta = build_meta(cache.fetched_at if cache else timezone.now(), cache.source_timestamp if cache else timezone.now(), 'fresh', MAX_STALE_SECONDS)
    return Response(wrap_cached_response(payload, meta))


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def house_monitoring_stats(request, house_id):
    """Get statistical aggregations for house monitoring data"""
    house = get_object_or_404(House, id=house_id)
    
    # Get period parameter (default 7 days)
    period = int(request.query_params.get('period', 7))
    
    stats = house.get_stats(days=period)
    
    if not stats:
        return Response({
            'status': 'no_data',
            'message': f'No monitoring data available for the last {period} days'
        }, status=status.HTTP_404_NOT_FOUND)
    
    serializer = HouseMonitoringStatsSerializer(stats)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def house_monitoring_kpis(request, house_id):
    """Get derived operational KPIs (cached-first by default)."""
    house = _house_from_scope_or_404(request, house_id)
    mode = _cache_mode(request)
    cache = HouseMonitoringCache.objects.filter(house=house).first()
    if mode != 'live' and cache and cache.kpis_payload:
        meta = build_meta(cache.fetched_at, cache.source_timestamp, cache.refresh_state, MAX_STALE_SECONDS)
        if mode == 'cached_then_live' and _should_refresh(meta):
            upsert_farm_monitoring_cache(house.farm)
            cache.refresh_from_db()
            meta = build_meta(cache.fetched_at, cache.source_timestamp, cache.refresh_state, MAX_STALE_SECONDS)
        return Response(wrap_cached_response(cache.kpis_payload, meta))

    scraper, err = _house_rotem_scraper_or_error(house)
    if err:
        return err

    # Live water/feed day-over-day from Rotem water history (CommandID 40).
    now = timezone.now()
    start_date = (now.date() - timedelta(days=7)).isoformat()
    end_date = now.date().isoformat()
    raw_water = scraper.get_water_history(house_number=house.house_number, start_date=start_date, end_date=end_date) or {}
    response_obj = raw_water.get('reponseObj', raw_water) if isinstance(raw_water, dict) else {}
    ds_data = response_obj.get('dsData', {}) if isinstance(response_obj, dict) else {}
    rows = ds_data.get('Data', []) if isinstance(ds_data, dict) else []
    water_by_day = {}
    feed_by_day = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        gday = row.get('HistoryRecord_GrowthDay')
        try:
            gday = int(gday)
        except (TypeError, ValueError):
            continue
        if house.batch_start_date:
            day = house.batch_start_date + timedelta(days=gday)
            day_key = day.isoformat()
        else:
            day_key = str(gday)
        w = _safe_float(row.get('HistoryRecord_DailyWater') or row.get('DailyWater') or row.get('Water'))
        f = _safe_float(row.get('HistoryRecord_DailyFeed') or row.get('DailyFeed') or row.get('Feed'))
        if w is not None:
            water_by_day[day_key] = w
        if f is not None:
            feed_by_day[day_key] = f

    sorted_water_days = sorted(water_by_day.keys())
    sorted_feed_days = sorted(feed_by_day.keys())
    water_today = water_by_day.get(sorted_water_days[-1]) if sorted_water_days else None
    water_yesterday = water_by_day.get(sorted_water_days[-2]) if len(sorted_water_days) > 1 else None
    feed_today = feed_by_day.get(sorted_feed_days[-1]) if sorted_feed_days else None
    feed_yesterday = feed_by_day.get(sorted_feed_days[-2]) if len(sorted_feed_days) > 1 else None

    # Live heater runtime from Rotem heater history (CommandID 43).
    heater_data = scraper.get_heater_history(house_number=house.house_number) or {}
    heater_records = heater_data.get('records', []) if isinstance(heater_data, dict) else []
    heater_hours_24h = None
    heater_cycles_24h = None
    if heater_records:
        last = heater_records[-1]
        heater_hours_24h = _safe_float(last.get('total_runtime_hours'))
        per_device = last.get('per_device', {}) if isinstance(last.get('per_device'), dict) else {}
        heater_cycles_24h = len([k for k, v in per_device.items() if isinstance(v, dict) and (v.get('minutes') or 0) > 0])

    def calc_delta(current, previous):
        if current is None or previous is None:
            return {'current': current, 'previous': previous, 'delta': None, 'delta_pct': None}
        delta = current - previous
        delta_pct = (delta / previous * 100.0) if previous != 0 else None
        return {'current': current, 'previous': previous, 'delta': delta, 'delta_pct': delta_pct}

    water_delta = calc_delta(water_today, water_yesterday)
    feed_delta = calc_delta(feed_today, feed_yesterday)
    ratio_today = (water_today / feed_today) if (water_today is not None and feed_today not in [None, 0]) else None
    ratio_yesterday = (water_yesterday / feed_yesterday) if (water_yesterday is not None and feed_yesterday not in [None, 0]) else None
    ratio_delta_pct = ((ratio_today - ratio_yesterday) / ratio_yesterday * 100.0) if (ratio_today is not None and ratio_yesterday not in [None, 0]) else None

    payload = {
        'house_id': house.id,
        'window_hours': 24,
        'day_over_day_context': None,
        'data_quality': {
            'snapshots_24h': None,
            'snapshots_7d': None,
            'enough_for_runtime': heater_hours_24h is not None,
            'enough_for_dod_delta': water_today is not None and water_yesterday is not None,
        },
        'heater_runtime': {
            'hours_24h': heater_hours_24h,
            'cycles_24h': heater_cycles_24h,
            'method': 'rotem_command_43_live',
        },
        'fan_runtime': {
            'hours_24h': None,
            'method': 'not_available_from_live_path',
        },
        'water_day_over_day': water_delta,
        'feed_day_over_day': feed_delta,
        'water_feed_ratio': {
            'today': ratio_today,
            'yesterday': ratio_yesterday,
            'delta_pct': ratio_delta_pct,
        },
        'ventilation_effort_index': None,
        'alarm_burden': {
            'total_24h': None,
            'critical_24h': None,
            'high_24h': None,
            'medium_24h': None,
            'low_24h': None,
            'active_now': None,
        },
    }
    HouseMonitoringCache.objects.update_or_create(
        house=house,
        defaults={
            'kpis_payload': payload,
            'source_timestamp': timezone.now(),
            'refresh_state': 'fresh',
            'last_error': '',
        },
    )
    cache = HouseMonitoringCache.objects.filter(house=house).first()
    meta = build_meta(cache.fetched_at if cache else timezone.now(), cache.source_timestamp if cache else timezone.now(), 'fresh', MAX_STALE_SECONDS)
    return Response(wrap_cached_response(payload, meta))


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def farm_houses_monitoring_all(request, farm_id):
    """Get latest monitoring for all houses in a farm (cached-first by default)."""
    farm = get_object_or_404(_scoped_farms_queryset(request), id=farm_id)
    mode = _cache_mode(request)
    cache = FarmMonitoringCache.objects.filter(farm=farm).first()
    if mode != 'live' and cache and cache.houses_payload:
        meta = build_meta(cache.fetched_at, cache.source_timestamp, cache.refresh_state, MAX_STALE_SECONDS)
        if mode == 'cached_then_live' and _should_refresh(meta):
            upsert_farm_monitoring_cache(farm)
            cache.refresh_from_db()
            meta = build_meta(cache.fetched_at, cache.source_timestamp, cache.refresh_state, MAX_STALE_SECONDS)
        return Response(wrap_cached_response(cache.houses_payload, meta))

    houses = list(House.objects.filter(farm=farm, is_active=True).order_by('house_number'))
    if not houses:
        payload = {'farm_id': farm_id, 'farm_name': farm.name, 'houses_count': 0, 'houses': []}
        return Response(wrap_cached_response(payload, build_meta(timezone.now(), timezone.now(), 'fresh', MAX_STALE_SECONDS)))

    scraper, err = _house_rotem_scraper_or_error(houses[0])
    if err:
        return err
    payload = scraper.get_site_controllers_info() or {}

    results = []
    for house in houses:
        live = _extract_live_house_from_site_controllers(payload, house.house_number)
        if live:
            results.append({
                'house_id': house.id,
                'house_number': house.house_number,
                'timestamp': live.get('timestamp'),
                'source_timestamp': live.get('source_timestamp'),
                'average_temperature': live.get('average_temperature'),
                'outside_temperature': None,
                'humidity': live.get('humidity'),
                'static_pressure': live.get('static_pressure'),
                'target_temperature': None,
                'ventilation_level': live.get('airflow_percentage'),
                'growth_day': house.age_days,
                'bird_count': None,
                'livability': None,
                'water_consumption': live.get('water_consumption'),
                'feed_consumption': live.get('feed_consumption'),
                'airflow_cfm': None,
                'airflow_percentage': live.get('airflow_percentage'),
                'connection_status': 'connected' if live.get('is_connected') else 'disconnected',
                'alarm_status': live.get('alarm_status') or 'normal',
                'has_alarms': False,
                'is_connected': bool(live.get('is_connected')),
            })
        else:
            results.append({
                'house_id': house.id,
                'house_number': house.house_number,
                'status': 'no_data',
                'message': 'No live Rotem data available for this house',
            })

    payload = {'farm_id': farm_id, 'farm_name': farm.name, 'houses_count': len(results), 'houses': results}
    FarmMonitoringCache.objects.update_or_create(
        farm=farm,
        defaults={
            'houses_payload': payload,
            'source_timestamp': timezone.now(),
            'refresh_state': 'fresh',
            'last_error': '',
        },
    )
    cache = FarmMonitoringCache.objects.filter(farm=farm).first()
    meta = build_meta(cache.fetched_at if cache else timezone.now(), cache.source_timestamp if cache else timezone.now(), 'fresh', MAX_STALE_SECONDS)
    return Response(wrap_cached_response(payload, meta))


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def farm_houses_monitoring_dashboard(request, farm_id):
    """Get dashboard data (cached-first by default)."""
    farm = get_object_or_404(_scoped_farms_queryset(request), id=farm_id)
    mode = _cache_mode(request)
    cache = FarmMonitoringCache.objects.filter(farm=farm).first()
    if mode != 'live' and cache and cache.dashboard_payload:
        meta = build_meta(cache.fetched_at, cache.source_timestamp, cache.refresh_state, MAX_STALE_SECONDS)
        if mode == 'cached_then_live' and _should_refresh(meta):
            upsert_farm_monitoring_cache(farm)
            cache.refresh_from_db()
            meta = build_meta(cache.fetched_at, cache.source_timestamp, cache.refresh_state, MAX_STALE_SECONDS)
        return Response(wrap_cached_response(cache.dashboard_payload, meta))

    houses = list(House.objects.filter(farm=farm, is_active=True).order_by('house_number'))
    dashboard_data = {
        'farm_id': farm_id,
        'farm_name': farm.name,
        'total_houses': len(houses),
        'houses': [],
        'alerts_summary': {'total_active': 0, 'critical': 0, 'warning': 0, 'normal': 0},
        'connection_summary': {'connected': 0, 'disconnected': 0},
    }
    if not houses:
        return Response(wrap_cached_response(dashboard_data, build_meta(timezone.now(), timezone.now(), 'fresh', MAX_STALE_SECONDS)))

    scraper, err = _house_rotem_scraper_or_error(houses[0])
    if err:
        return err
    payload = scraper.get_site_controllers_info() or {}

    for house in houses:
        live = _extract_live_house_from_site_controllers(payload, house.house_number)
        house_data = {
            'house_id': house.id,
            'house_number': house.house_number,
            'current_day': house.age_days,
            'status': house.status,
            'active_alarms_count': 0,
        }
        if not live:
            house_data['status'] = 'no_data'
            dashboard_data['houses'].append(house_data)
            continue

        alarm_status = live.get('alarm_status') or 'normal'
        house_data.update({
            'timestamp': live.get('timestamp'),
            'source_timestamp': live.get('source_timestamp'),
            'average_temperature': live.get('average_temperature'),
            'humidity': live.get('humidity'),
            'static_pressure': live.get('static_pressure'),
            'airflow_percentage': live.get('airflow_percentage'),
            'water_consumption': live.get('water_consumption'),
            'feed_consumption': live.get('feed_consumption'),
            'is_connected': bool(live.get('is_connected')),
            'alarm_status': alarm_status,
        })

        if house_data['is_connected']:
            dashboard_data['connection_summary']['connected'] += 1
        else:
            dashboard_data['connection_summary']['disconnected'] += 1

        if alarm_status == 'critical':
            dashboard_data['alerts_summary']['critical'] += 1
        elif alarm_status == 'warning':
            dashboard_data['alerts_summary']['warning'] += 1
        else:
            dashboard_data['alerts_summary']['normal'] += 1

        dashboard_data['houses'].append(house_data)

    FarmMonitoringCache.objects.update_or_create(
        farm=farm,
        defaults={
            'dashboard_payload': dashboard_data,
            'source_timestamp': timezone.now(),
            'refresh_state': 'fresh',
            'last_error': '',
        },
    )
    cache = FarmMonitoringCache.objects.filter(farm=farm).first()
    meta = build_meta(cache.fetched_at if cache else timezone.now(), cache.source_timestamp if cache else timezone.now(), 'fresh', MAX_STALE_SECONDS)
    return Response(wrap_cached_response(dashboard_data, meta))


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def house_details(request, house_id):
    """Get comprehensive house details including monitoring, devices, flock, tasks, and feed"""
    house = get_object_or_404(House, id=house_id)
    
    # Get latest snapshot
    snapshot = house.get_latest_snapshot()
    
    # Get active alarms
    active_alarms = HouseAlarm.objects.filter(house=house, is_active=True)
    
    # Get tasks for this house
    from tasks.models import Task
    from tasks.serializers import TaskSerializer
    tasks = Task.objects.filter(house=house).order_by('day_offset', 'task_name')
    
    # Group tasks by status
    current_day = house.current_day
    upcoming_tasks = []
    past_tasks = []
    today_tasks = []
    completed_tasks = []
    
    for task in tasks:
        if task.is_completed:
            completed_tasks.append(task)
        elif current_day is not None:
            if task.day_offset < current_day:
                past_tasks.append(task)
            elif task.day_offset == current_day:
                today_tasks.append(task)
            else:
                upcoming_tasks.append(task)
        else:
            upcoming_tasks.append(task)
    
    # Build comprehensive response (heater CommandID 43 history: load via dedicated endpoints on demand)
    details = {
        'house': HouseSerializer(house).data,
        'monitoring': HouseMonitoringSnapshotSerializer(snapshot).data if snapshot else None,
        'alarms': HouseAlarmSerializer(active_alarms, many=True).data,
        'stats': house.get_stats(days=7) if snapshot else None,
        'tasks': {
            'all': TaskSerializer(tasks, many=True).data,
            'today': TaskSerializer(today_tasks, many=True).data,
            'upcoming': TaskSerializer(upcoming_tasks, many=True).data,
            'past': TaskSerializer(past_tasks, many=True).data,
            'completed': TaskSerializer(completed_tasks, many=True).data,
            'total': tasks.count(),
            'completed_count': len(completed_tasks),
            'pending_count': tasks.count() - len(completed_tasks),
        },
    }
    
    return Response(details)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def house_heater_history(request, house_id):
    """Get house heater history (cached-first by default)."""
    house = _house_from_scope_or_404(request, house_id)
    mode = _cache_mode(request)
    cache = HouseMonitoringCache.objects.filter(house=house).first()
    if mode != 'live' and cache and cache.heater_payload:
        meta = build_meta(cache.fetched_at, cache.source_timestamp, cache.refresh_state, MAX_STALE_SECONDS)
        if mode == 'cached_then_live' and _should_refresh(meta):
            upsert_farm_monitoring_cache(house.farm)
            cache.refresh_from_db()
            meta = build_meta(cache.fetched_at, cache.source_timestamp, cache.refresh_state, MAX_STALE_SECONDS)
        return Response(wrap_cached_response(cache.heater_payload, meta))

    scraper, err = _house_rotem_scraper_or_error(house)
    if err:
        return err

    parsed = scraper.get_heater_history(house_number=house.house_number) or {}
    records = parsed.get('records', []) if isinstance(parsed, dict) else []
    daily = []
    for r in records:
        growth_day = r.get('growth_day')
        if growth_day is None:
            continue
        dt = None
        if house.batch_start_date:
            try:
                dt = house.batch_start_date + timedelta(days=int(growth_day))
            except (TypeError, ValueError):
                dt = None
        daily.append({
            'growth_day': int(growth_day),
            'date': dt.isoformat() if dt else None,
            'total_hours': _safe_float(r.get('total_runtime_hours')) or 0.0,
            'total_minutes': int(r.get('total_runtime_minutes') or 0),
            'device_breakdown': r.get('per_device', {}),
        })
    daily.sort(key=lambda row: row.get('growth_day', 0))
    payload = {'heater_history': {'daily': daily}}
    HouseMonitoringCache.objects.update_or_create(
        house=house,
        defaults={
            'heater_payload': payload,
            'source_timestamp': timezone.now(),
            'refresh_state': 'fresh',
            'last_error': '',
        },
    )
    cache = HouseMonitoringCache.objects.filter(house=house).first()
    meta = build_meta(cache.fetched_at if cache else timezone.now(), cache.source_timestamp if cache else timezone.now(), 'fresh', MAX_STALE_SECONDS)
    return Response(wrap_cached_response(payload, meta))


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def house_heater_history_refresh(request, house_id):
    """Fetch CommandID 43 from Rotem, update cache, return serialized heater history."""
    house = get_object_or_404(House, id=house_id)
    result = sync_refresh_house_heater_history(house.id)
    if result.get("status") == "success":
        return Response(
            {
                "heater_history": build_heater_history_payload(house),
                "refresh_result": result,
            }
        )
    status_code = status.HTTP_400_BAD_REQUEST
    if result.get("reason") in ("login_failed", "empty_response"):
        status_code = status.HTTP_502_BAD_GATEWAY
    return Response(
        {"error": result.get("reason", "refresh_failed"), "refresh_result": result},
        status=status_code,
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def farm_monitoring_refresh(request, farm_id):
    """Force-refresh cached monitoring bundle for a farm."""
    farm = get_object_or_404(_scoped_farms_queryset(request), id=farm_id)
    result = upsert_farm_monitoring_cache(farm)
    cache = FarmMonitoringCache.objects.filter(farm=farm).first()
    meta = build_meta(
        fetched_at=cache.fetched_at if cache else timezone.now(),
        source_timestamp=cache.source_timestamp if cache else timezone.now(),
        refresh_state=cache.refresh_state if cache else ('failed' if result.status != 'success' else 'fresh'),
        stale_seconds=MAX_STALE_SECONDS,
    )
    return Response(
        {
            'status': result.status,
            'message': result.message,
            'farms_processed': result.farms_processed,
            'houses_processed': result.houses_processed,
            'meta': meta,
        },
        status=status.HTTP_200_OK if result.status in ('success', 'partial') else status.HTTP_502_BAD_GATEWAY,
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def houses_comparison(request):
    """Get houses comparison data (cached-first by default)."""
    # Get query parameters
    farm_id = request.query_params.get('farm_id')
    mode = _cache_mode(request)
    if farm_id and mode != 'live':
        scoped_farm = get_object_or_404(_scoped_farms_queryset(request), id=farm_id)
        cache = FarmMonitoringCache.objects.filter(farm=scoped_farm).first()
        if cache and cache.comparison_payload:
            meta = build_meta(cache.fetched_at, cache.source_timestamp, cache.refresh_state, MAX_STALE_SECONDS)
            if mode == 'cached_then_live' and _should_refresh(meta):
                upsert_farm_monitoring_cache(scoped_farm)
                cache.refresh_from_db()
                meta = build_meta(cache.fetched_at, cache.source_timestamp, cache.refresh_state, MAX_STALE_SECONDS)
            return Response(wrap_cached_response(cache.comparison_payload, meta))

    house_ids = request.query_params.getlist('house_ids')
    favorites_only = request.query_params.get('favorites', 'false').lower() == 'true'
    
    # Build queryset (scoped) and select farm for grouped live calls.
    houses = _scoped_houses_queryset(request).filter(is_active=True).select_related('farm')
    
    if farm_id:
        houses = houses.filter(farm_id=farm_id)
    
    if house_ids:
        houses = houses.filter(id__in=house_ids)
    
    # TODO: Implement favorites when user preferences are added
    # if favorites_only:
    #     houses = houses.filter(id__in=user_favorite_house_ids)
    
    comparison_data = []
    now = timezone.now()
    live_by_farm = {}
    for farm_id_value in {h.farm_id for h in houses}:
        farm_houses = [h for h in houses if h.farm_id == farm_id_value]
        if not farm_houses:
            continue
        scraper, err = _house_rotem_scraper_or_error(farm_houses[0])
        if err:
            continue
        live_by_farm[farm_id_value] = scraper.get_site_controllers_info() or {}

    for house in houses:
        age_days = house.age_days
        is_full_house = age_days is not None and age_days >= 0
        farm_payload = live_by_farm.get(house.farm_id, {})
        live = _extract_live_house_from_site_controllers(farm_payload, house.house_number) or {}
        response_obj = farm_payload.get('reponseObj', {}) if isinstance(farm_payload, dict) else {}

        water_consumption = _safe_float(
            _extract_comparison_item(response_obj, 'Water_Daily', house.house_number)
        )
        if water_consumption is None:
            water_consumption = live.get('water_consumption')
        feed_consumption = _safe_float(
            _extract_comparison_item(response_obj, 'Feed_Daily', house.house_number)
        )
        if feed_consumption is None:
            feed_consumption = live.get('feed_consumption')
        bird_count = _safe_float(_extract_comparison_item(response_obj, 'Current_Birds_Count_In_House', house.house_number))
        bird_count = int(bird_count) if bird_count is not None else None
        water_per_bird = (
            (float(water_consumption) / float(bird_count))
            if (water_consumption is not None and bird_count not in [None, 0])
            else None
        )
        feed_per_bird = (
            (float(feed_consumption) / float(bird_count))
            if (feed_consumption is not None and bird_count not in [None, 0])
            else None
        )
        water_feed_ratio = (
            (float(water_consumption) / float(feed_consumption))
            if (water_consumption is not None and feed_consumption not in [None, 0])
            else None
        )

        # Freshness in minutes since last live update.
        data_freshness_minutes = None
        source_ts = live.get('source_timestamp')
        if source_ts:
            try:
                dt = datetime.fromisoformat(str(source_ts).replace('Z', '+00:00'))
                data_freshness_minutes = max(int((now - dt).total_seconds() / 60), 0)
            except ValueError:
                data_freshness_minutes = None

        heater_raw = _extract_comparison_item(response_obj, 'Heaters', house.house_number)
        fan_raw = _extract_comparison_item(response_obj, 'Tunnel_Fans', house.house_number) or _extract_comparison_item(response_obj, 'Exh_Fans', house.house_number)
        heater_on = bool(heater_raw and str(heater_raw).lower() not in ('langkey_off', 'off', '0', 'false', 'none', ''))
        fan_on = bool(fan_raw and str(fan_raw).lower() not in ('langkey_off', 'off', '0', 'false', 'none', ''))
        wind_speed = _safe_float(_extract_comparison_item(response_obj, 'Wind_Speed', house.house_number))
        wind_direction = _safe_float(_extract_comparison_item(response_obj, 'Wind_Direction', house.house_number))
        wind_chill_temperature = _safe_float(_extract_comparison_item(response_obj, 'Wind_Chill_Temperature', house.house_number))

        house_comparison = {
            'house_id': house.id,
            'house_number': house.house_number,
            'farm_id': house.farm.id,
            'farm_name': house.farm.name,
            
            # House Status - use age_days for consistency (prefers Rotem age over calculated)
            'current_day': age_days,
            'age_days': age_days,
            'current_age_days': house.current_age_days,
            'is_integrated': house.is_integrated,
            'status': house.status,
            'is_full_house': is_full_house,
            
            # Time
            'last_update_time': source_ts or now,
            
            # Metrics - Temperature
            'average_temperature': live.get('average_temperature'),
            'outside_temperature': _safe_float(_extract_comparison_item(response_obj, 'Outside_Temperature', house.house_number)),
            'tunnel_temperature': _safe_float(_extract_comparison_item(response_obj, 'Tunnel_Temperature', house.house_number)),
            'target_temperature': _safe_float(_extract_comparison_item(response_obj, 'Set_Temperature', house.house_number)),
            
            # Metrics - Environment
            'static_pressure': live.get('static_pressure'),
            'inside_humidity': live.get('humidity'),
            'ventilation_mode': _extract_comparison_item(response_obj, 'Vent_Mode', house.house_number),
            'ventilation_level': _safe_float(_extract_comparison_item(response_obj, 'Vent_Level', house.house_number)),
            'airflow_cfm': _safe_float(str(_extract_comparison_item(response_obj, 'Current_Level_CFM', house.house_number) or '').replace(',', '')),
            'airflow_percentage': live.get('airflow_percentage'),
            
            # Metrics - Consumption (Daily)
            'water_consumption': water_consumption,
            'feed_consumption': feed_consumption,
            'water_per_bird': water_per_bird,
            'feed_per_bird': feed_per_bird,
            'water_feed_ratio': water_feed_ratio,
            
            # Metrics - Bird Status
            'bird_count': bird_count,
            'livability': _safe_float(_extract_comparison_item(response_obj, 'Livablity_Percents', house.house_number)),
            'growth_day': age_days,
            
            # Additional status
            'is_connected': bool(live.get('is_connected')),
            'has_alarms': False,
            'alarm_status': live.get('alarm_status') or 'normal',
            'active_alarms_count': None,
            'data_freshness_minutes': data_freshness_minutes,
            'heater_on': heater_on,
            'fan_on': fan_on,
            'wind_speed': wind_speed,
            'wind_direction': wind_direction,
            'wind_chill_temperature': wind_chill_temperature,
        }
        comparison_data.append(house_comparison)
    
    # Sort by farm name, then house number
    comparison_data.sort(key=lambda x: (x['farm_name'], x['house_number']))
    
    serializer = HouseComparisonSerializer(comparison_data, many=True)
    payload = {
        'count': len(serializer.data),
        'houses': serializer.data
    }
    if farm_id:
        scoped_farm = get_object_or_404(_scoped_farms_queryset(request), id=farm_id)
        FarmMonitoringCache.objects.update_or_create(
            farm=scoped_farm,
            defaults={
                'comparison_payload': payload,
                'source_timestamp': timezone.now(),
                'refresh_state': 'fresh',
                'last_error': '',
            },
        )
        cache = FarmMonitoringCache.objects.filter(farm=scoped_farm).first()
        meta = build_meta(cache.fetched_at if cache else timezone.now(), cache.source_timestamp if cache else timezone.now(), 'fresh', MAX_STALE_SECONDS)
        return Response(wrap_cached_response(payload, meta))
    return Response(wrap_cached_response(payload, build_meta(timezone.now(), timezone.now(), 'fresh', MAX_STALE_SECONDS)))


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def house_devices(request, house_id):
    """Get all devices for a house or create a new device"""
    house = get_object_or_404(House, id=house_id)
    
    if request.method == 'GET':
        devices = Device.objects.filter(house=house)
        serializer = DeviceSerializer(devices, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        serializer = DeviceSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(house=house)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def device_detail(request, device_id):
    """Get, update, or delete a specific device"""
    device = get_object_or_404(Device, id=device_id)
    
    if request.method == 'GET':
        serializer = DeviceSerializer(device)
        return Response(serializer.data)
    
    elif request.method in ['PUT', 'PATCH']:
        serializer = DeviceSerializer(device, data=request.data, partial=request.method == 'PATCH')
        if serializer.is_valid():
            serializer.save()
            # Create status history record
            DeviceStatus.objects.create(
                device=device,
                status=device.status,
                percentage=device.percentage,
                notes=f"Updated via API"
            )
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        device.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def device_control(request, device_id):
    """Control a device (turn on/off, set percentage, etc.)"""
    device = get_object_or_404(Device, id=device_id)
    
    action = request.data.get('action')  # 'on', 'off', 'set_percentage'
    percentage = request.data.get('percentage')
    
    if action == 'on':
        device.status = 'on'
    elif action == 'off':
        device.status = 'off'
    elif action == 'set_percentage' and percentage is not None:
        device.status = 'on'
        device.percentage = max(0, min(100, float(percentage)))
    else:
        return Response(
            {'error': 'Invalid action or missing parameters'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    device.save()
    
    # Create status history record
    DeviceStatus.objects.create(
        device=device,
        status=device.status,
        percentage=device.percentage,
        notes=f"Controlled via API: {action}"
    )
    
    serializer = DeviceSerializer(device)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def device_status_history(request, device_id):
    """Get status history for a device"""
    device = get_object_or_404(Device, id=device_id)
    
    limit = int(request.query_params.get('limit', 100))
    start_date = request.query_params.get('start_date')
    end_date = request.query_params.get('end_date')
    
    history = DeviceStatus.objects.filter(device=device)
    
    if start_date:
        try:
            start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            history = history.filter(timestamp__gte=start_date)
        except (ValueError, AttributeError):
            pass
    
    if end_date:
        try:
            end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            history = history.filter(timestamp__lte=end_date)
        except (ValueError, AttributeError):
            pass
    
    history = history[:limit]
    serializer = DeviceStatusSerializer(history, many=True)
    return Response(serializer.data)


@api_view(['GET', 'PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def house_control_settings(request, house_id):
    """Get or update control settings for a house"""
    house = get_object_or_404(House, id=house_id)
    
    # Get or create control settings
    control_settings, created = ControlSettings.objects.get_or_create(house=house)
    
    if request.method == 'GET':
        serializer = ControlSettingsSerializer(control_settings)
        return Response(serializer.data)
    
    elif request.method in ['PUT', 'PATCH']:
        serializer = ControlSettingsSerializer(
            control_settings,
            data=request.data,
            partial=request.method == 'PATCH'
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def temperature_curve(request, house_id):
    """Get or update temperature curve for a house"""
    house = get_object_or_404(House, id=house_id)
    control_settings, _ = ControlSettings.objects.get_or_create(house=house)
    
    if request.method == 'GET':
        curves = TemperatureCurve.objects.filter(control_settings=control_settings)
        serializer = TemperatureCurveSerializer(curves, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        # Update or create temperature curve points
        curve_data = request.data
        if isinstance(curve_data, list):
            # Bulk update
            TemperatureCurve.objects.filter(control_settings=control_settings).delete()
            curves = []
            for item in curve_data:
                curve = TemperatureCurve.objects.create(
                    control_settings=control_settings,
                    day=item['day'],
                    target_temperature=item['target_temperature'],
                    notes=item.get('notes', '')
                )
                curves.append(curve)
            serializer = TemperatureCurveSerializer(curves, many=True)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            # Single curve point
            serializer = TemperatureCurveSerializer(data=curve_data)
            if serializer.is_valid():
                serializer.save(control_settings=control_settings)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def house_configuration(request, house_id):
    """Get or update house configuration"""
    house = get_object_or_404(House, id=house_id)
    config, created = HouseConfiguration.objects.get_or_create(house=house)
    
    if request.method == 'GET':
        serializer = HouseConfigurationSerializer(config)
        return Response(serializer.data)
    
    elif request.method in ['PUT', 'PATCH']:
        serializer = HouseConfigurationSerializer(
            config,
            data=request.data,
            partial=request.method == 'PATCH'
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def house_sensors(request, house_id):
    """Get or create sensors for a house"""
    house = get_object_or_404(House, id=house_id)
    
    if request.method == 'GET':
        sensors = Sensor.objects.filter(house=house)
        serializer = SensorSerializer(sensors, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        serializer = SensorSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(house=house)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_water_forecast(request, house_id):
    """Generate short-horizon water forecasts (24/48/72h) for a house."""
    house = get_object_or_404(House, id=house_id)
    service = WaterForecastService()
    forecasts = service.generate_forecasts(house)
    serializer = WaterConsumptionForecastSerializer(forecasts, many=True)
    return Response({
        'status': 'success',
        'house_id': house.id,
        'generated': len(serializer.data),
        'results': serializer.data,
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_water_forecasts(request, house_id):
    """List persisted water forecasts for a house."""
    house = get_object_or_404(_scoped_houses_queryset(request), id=house_id)
    qs = WaterConsumptionForecast.objects.filter(house=house).order_by('-forecast_date')[:20]
    serializer = WaterConsumptionForecastSerializer(qs, many=True)
    return Response({'count': len(serializer.data), 'results': serializer.data})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_water_alerts(request, house_id):
    """List water alerts with optional lifecycle filters."""
    house = get_object_or_404(_scoped_houses_queryset(request), id=house_id)
    include_resolved = request.query_params.get('include_resolved', 'false').lower() == 'true'
    include_snoozed = request.query_params.get('include_snoozed', 'true').lower() == 'true'
    qs = WaterConsumptionAlert.objects.filter(house=house).order_by('-created_at')
    if not include_resolved:
        qs = qs.filter(is_resolved=False)
    if not include_snoozed:
        now = timezone.now()
        qs = qs.filter(Q(snoozed_until__isnull=True) | Q(snoozed_until__lte=now))
    serializer = WaterConsumptionAlertSerializer(qs[:100], many=True)
    return Response({'count': len(serializer.data), 'results': serializer.data})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def acknowledge_water_alert(request, alert_id):
    """Acknowledge a water alert."""
    alert = get_object_or_404(_scoped_water_alerts_queryset(request), id=alert_id)
    alert.acknowledge(user=request.user)
    return Response(WaterConsumptionAlertSerializer(alert).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def resolve_water_alert(request, alert_id):
    """Resolve a water alert."""
    alert = get_object_or_404(_scoped_water_alerts_queryset(request), id=alert_id)
    alert.resolve(user=request.user)
    return Response(WaterConsumptionAlertSerializer(alert).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def snooze_water_alert(request, alert_id):
    """Snooze a water alert by N hours (default 6)."""
    alert = get_object_or_404(_scoped_water_alerts_queryset(request), id=alert_id)
    hours = int(request.data.get('hours', 6))
    until = timezone.now() + timedelta(hours=max(hours, 1))
    alert.snooze(until)
    return Response(WaterConsumptionAlertSerializer(alert).data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def water_alerts_feed(request):
    """Cross-farm water alerts feed for mobile alerts center."""
    include_resolved = request.query_params.get('include_resolved', 'false').lower() == 'true'
    include_snoozed = request.query_params.get('include_snoozed', 'true').lower() == 'true'
    status_filter = request.query_params.get('status')  # unread|acknowledged|resolved|all
    severity = request.query_params.get('severity')
    farm_id = request.query_params.get('farm_id')

    qs = _scoped_water_alerts_queryset(request).order_by('-created_at')
    if farm_id:
        qs = qs.filter(house__farm_id=farm_id)
    if severity:
        qs = qs.filter(severity__iexact=severity)
    if not include_resolved:
        qs = qs.filter(is_resolved=False)
    if not include_snoozed:
        now = timezone.now()
        qs = qs.filter(Q(snoozed_until__isnull=True) | Q(snoozed_until__lte=now))
    if status_filter and status_filter != 'all':
        if status_filter == 'unread':
            qs = qs.filter(is_acknowledged=False, is_resolved=False)
        elif status_filter == 'acknowledged':
            qs = qs.filter(is_acknowledged=True, is_resolved=False)
        elif status_filter == 'resolved':
            qs = qs.filter(is_resolved=True)

    serializer = WaterConsumptionAlertSerializer(qs[:300], many=True)
    return Response({'count': len(serializer.data), 'results': serializer.data})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def trigger_water_anomaly_detection(request, house_id=None):
    """
    Trigger water consumption anomaly detection on demand
    
    Can be called with:
    - house_id in URL path: Check specific house
    - farm_id in request body: Check all houses in farm
    - No parameters: Check all Rotem-integrated houses
    
    If Celery workers are not available, runs synchronously as fallback.
    """
    from houses.tasks import monitor_water_consumption
    from celery.result import AsyncResult
    from django.conf import settings
    import logging
    import uuid
    
    logger = logging.getLogger(__name__)
    
    try:
        farm_id = request.data.get('farm_id')
        run_sync = request.data.get('run_sync', False)  # Allow forcing synchronous execution
        correlation_id = request.data.get('correlation_id') or str(uuid.uuid4())
        
        # Import the implementation function for synchronous execution
        from houses.tasks import monitor_water_consumption_impl
        
        # Check if we should run synchronously (if CELERY_TASK_ALWAYS_EAGER is set or run_sync is True)
        if getattr(settings, 'CELERY_TASK_ALWAYS_EAGER', False) or run_sync:
            logger.info(
                f"Running water consumption monitoring synchronously (house_id={house_id}, farm_id={farm_id})",
                extra={"correlation_id": correlation_id, "house_id": house_id, "farm_id": farm_id},
            )
            # Run synchronously using the implementation function
            result = monitor_water_consumption_impl(house_id=house_id, farm_id=farm_id, run_id=correlation_id)
            
            return Response({
                'status': 'success',
                'message': 'Water consumption anomaly detection completed',
                'task_id': None,
                'house_id': house_id,
                'farm_id': farm_id,
                'correlation_id': correlation_id,
                'result': result,
                'house_results': result.get('house_results', []),
                'execution_mode': 'synchronous',
            }, status=status.HTTP_200_OK)
        
        # Try to run asynchronously
        try:
            task_result = monitor_water_consumption.delay(house_id=house_id, farm_id=farm_id, run_id=correlation_id)
            
            # Check if task is actually queued (not stuck in PENDING)
            # Wait a moment to see if it gets picked up
            import time
            time.sleep(0.5)
            
            async_result = AsyncResult(task_result.id)
            if async_result.state == 'PENDING':
                # Task is still pending - workers might not be running
                # Check if we can connect to the broker
                try:
                    from celery import current_app
                    inspect = current_app.control.inspect()
                    active_workers = inspect.active()
                    
                    if not active_workers:
                        # No active workers, run synchronously as fallback
                        logger.warning("No Celery workers available, running synchronously as fallback")
                        result = monitor_water_consumption_impl(house_id=house_id, farm_id=farm_id, run_id=correlation_id)
                        
                        return Response({
                            'status': 'success',
                            'message': 'Water consumption anomaly detection completed (ran synchronously - no workers available)',
                            'task_id': None,
                            'house_id': house_id,
                            'farm_id': farm_id,
                            'correlation_id': correlation_id,
                            'result': result,
                            'house_results': result.get('house_results', []),
                            'execution_mode': 'synchronous_fallback',
                            'warning': 'Celery workers are not running. Task executed synchronously.',
                        }, status=status.HTTP_200_OK)
                except Exception as inspect_error:
                    logger.warning(f"Could not inspect Celery workers: {inspect_error}. Running synchronously as fallback.")
                    result = monitor_water_consumption_impl(house_id=house_id, farm_id=farm_id, run_id=correlation_id)
                    
                    return Response({
                        'status': 'success',
                        'message': 'Water consumption anomaly detection completed (ran synchronously)',
                        'task_id': None,
                        'house_id': house_id,
                        'farm_id': farm_id,
                        'correlation_id': correlation_id,
                        'result': result,
                        'house_results': result.get('house_results', []),
                        'execution_mode': 'synchronous_fallback',
                        'warning': 'Could not verify Celery workers. Task executed synchronously.',
                    }, status=status.HTTP_200_OK)
            
            logger.info(f"Triggered water consumption monitoring task {task_result.id} (house_id={house_id}, farm_id={farm_id})")
            
            return Response({
                'status': 'success',
                'message': 'Water consumption anomaly detection started',
                'task_id': task_result.id,
                'house_id': house_id,
                'farm_id': farm_id,
                'correlation_id': correlation_id,
                'execution_mode': 'asynchronous',
            }, status=status.HTTP_202_ACCEPTED)
        
        except Exception as celery_error:
            # Celery error - fallback to synchronous execution
            logger.warning(f"Celery task submission failed: {celery_error}. Running synchronously as fallback.")
            result = monitor_water_consumption_impl(house_id=house_id, farm_id=farm_id, run_id=correlation_id)
            
            return Response({
                'status': 'success',
                'message': 'Water consumption anomaly detection completed (ran synchronously)',
                'task_id': None,
                'house_id': house_id,
                'farm_id': farm_id,
                'correlation_id': correlation_id,
                'result': result,
                'house_results': result.get('house_results', []),
                'execution_mode': 'synchronous_fallback',
                'warning': f'Celery unavailable: {str(celery_error)}. Task executed synchronously.',
            }, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f"Error triggering water anomaly detection: {str(e)}", exc_info=True)
        return Response({
            'status': 'error',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_water_anomaly_detection_status(request, task_id):
    """
    Check the status and results of a water consumption anomaly detection task
    """
    from celery.result import AsyncResult
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        # Get task result
        task_result = AsyncResult(task_id)
        
        # Check task state
        task_state = task_result.state
        
        response_data = {
            'task_id': task_id,
            'state': task_state,
        }
        
        if task_state == 'PENDING':
            response_data['status'] = 'pending'
            response_data['message'] = 'Task is waiting to be processed'
        elif task_state == 'PROGRESS':
            response_data['status'] = 'running'
            response_data['message'] = 'Task is currently running'
            # Include progress info if available
            if task_result.info:
                response_data['info'] = task_result.info
        elif task_state == 'SUCCESS':
            response_data['status'] = 'success'
            response_data['message'] = 'Task completed successfully'
            # Get the result
            result = task_result.result
            if isinstance(result, dict):
                response_data.update({
                    'houses_checked': result.get('houses_checked', 0),
                    'alerts_created': result.get('alerts_created', 0),
                    'emails_sent': result.get('emails_sent', 0),
                    'timestamp': result.get('timestamp'),
                })
            else:
                response_data['result'] = result
        elif task_state == 'FAILURE':
            response_data['status'] = 'failure'
            response_data['message'] = 'Task failed'
            # Get error info
            try:
                response_data['error'] = str(task_result.info)
            except:
                response_data['error'] = 'Unknown error occurred'
        else:
            response_data['status'] = 'unknown'
            response_data['message'] = f'Task state: {task_state}'
        
        return Response(response_data, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f"Error checking task status: {str(e)}", exc_info=True)
        return Response({
            'status': 'error',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def sync_flock_from_rotem(request, house_id):
    """
    Upsert the active flock for this house from Rotem-derived house fields
    (batch_start_date / chicken_in_date, age, monitoring bird count).
    """
    house = get_object_or_404(House, pk=house_id)
    try:
        flock, created = upsert_active_flock_from_rotem(house, request.user)
    except ValueError as e:
        return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    serializer = FlockSerializer(flock, context={'request': request})
    return Response(
        {
            'flock': serializer.data,
            'created': created,
            'message': 'Flock synced from Rotem integration.',
        },
        status=status.HTTP_200_OK,
    )
