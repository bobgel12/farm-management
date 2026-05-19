from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q, Avg, Max, Min
from django.utils import timezone
from datetime import timedelta, datetime, date
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
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
    HouseDailySummary,
    FlockRiskScore,
)
from .serializers import (
    HouseSerializer, HouseListSerializer,
    HouseMonitoringSnapshotSerializer, HouseMonitoringSummarySerializer,
    HouseMonitoringStatsSerializer, HouseAlarmSerializer,
    HouseComparisonSerializer, DeviceSerializer, DeviceStatusSerializer,
    ControlSettingsSerializer, TemperatureCurveSerializer,
    HouseConfigurationSerializer, SensorSerializer,
    WaterConsumptionAlertSerializer, WaterConsumptionForecastSerializer,
    HouseDailySummarySerializer, FlockRiskScoreSerializer,
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
    cache_is_fresh,
    upsert_farm_monitoring_cache,
    wrap_cached_response,
)
from .models import FarmMonitoringCache, HouseMonitoringCache
from rotem_scraper.tasks import sync_refresh_house_heater_history
from farms.views import user_accessible_organization_ids
from rotem_scraper.scraper import RotemScraper

logger = logging.getLogger(__name__)


def _cache_mode(request):
    mode = (request.query_params.get('mode') or 'cached_then_live').lower()
    if mode not in ('cached', 'live', 'cached_then_live'):
        return 'cached'
    return mode


def _should_refresh(meta: dict):
    return bool(meta.get('is_stale')) and meta.get('refresh_state') != 'refreshing'


def _ensure_farm_cache(farm: Farm, force: bool = False):
    """Read-through farm cache: refresh from Rotem when missing or older than TTL."""
    cache = FarmMonitoringCache.objects.filter(farm=farm).first()
    has_payload = bool(cache and (cache.houses_payload or cache.dashboard_payload))
    if force or not cache_is_fresh(cache) or not has_payload:
        upsert_farm_monitoring_cache(farm)
        cache = FarmMonitoringCache.objects.filter(farm=farm).first()
    return cache


def _ensure_house_cache(house: House, field_name: str, force: bool = False):
    """Refresh the farm bundle when a house cache field is missing or stale."""
    cache = HouseMonitoringCache.objects.filter(house=house).first()
    payload = getattr(cache, field_name, None) if cache else None
    if force or not cache_is_fresh(cache) or not payload:
        upsert_farm_monitoring_cache(house.farm)
        cache = HouseMonitoringCache.objects.filter(house=house).first()
    return cache


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
        if isinstance(value, str):
            value = value.strip().replace(',', '')
            if value in {'', '- - -', 'N/A', '---', 'null'}:
                return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _extract_current_numeric(house_data: dict, key: str):
    section = house_data.get(key, {}) if isinstance(house_data, dict) else {}
    if not isinstance(section, dict):
        return None
    for value_key in (
        'CurrentNumericValue',
        'CurrentValue',
        'Value',
        'NumericValue',
        'ParameterValue',
        'DisplayValue',
        'Text',
    ):
        value = _safe_float(section.get(value_key))
        if value is not None:
            return value
    return None


def _first_non_zero(*values):
    fallback = None
    for value in values:
        parsed = _safe_float(value)
        if parsed is None:
            continue
        if fallback is None:
            fallback = parsed
        if parsed != 0:
            return parsed
    return fallback


def _parse_site_controllers_source_timestamp(payload: dict):
    response_obj = payload.get('reponseObj') if isinstance(payload, dict) else None
    last_update = response_obj.get('LastUpdateDT') if isinstance(response_obj, dict) else None
    if isinstance(last_update, str):
        try:
            return datetime.fromisoformat(last_update.replace('Z', '+00:00'))
        except ValueError:
            return None
    return None


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
    average_temperature = _first_non_zero(
        _extract_current_numeric(data, 'Temperature'),
        _extract_comparison_item(response_obj, 'Average_Temperature', house_number),
        _extract_comparison_item(response_obj, 'Tunnel_Temperature', house_number),
        _extract_comparison_item(response_obj, 'Temperature', house_number),
    )
    humidity = _first_non_zero(
        _extract_current_numeric(data, 'Humidity'),
        _extract_comparison_item(response_obj, 'Inside_Humidity', house_number),
        _extract_comparison_item(response_obj, 'Humidity', house_number),
    )
    static_pressure = _first_non_zero(
        _extract_current_numeric(data, 'Pressure'),
        _extract_comparison_item(response_obj, 'Static_Pressure', house_number),
        _extract_comparison_item(response_obj, 'Pressure', house_number),
    )
    airflow_percentage = _first_non_zero(
        _extract_current_numeric(data, 'VentLevel'),
        _extract_comparison_item(response_obj, 'Vent_Level', house_number),
        _extract_comparison_item(response_obj, 'Ventilation_Level', house_number),
    )
    water_consumption = _first_non_zero(
        _extract_current_numeric(data, 'DailyWater'),
        _extract_comparison_item(response_obj, 'Water_Daily', house_number),
    )
    feed_consumption = _first_non_zero(
        _extract_current_numeric(data, 'DailyFeed'),
        _extract_comparison_item(response_obj, 'Feed_Daily', house_number),
    )

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


def _parse_int_query_param(raw_value, default: int, minimum: int, maximum: int) -> int:
    try:
        parsed = int(raw_value)
    except (TypeError, ValueError):
        parsed = default
    return min(max(parsed, minimum), maximum)


def _trim_history_rows(rows, days: int):
    rows = list(rows or [])
    return rows[-days:] if len(rows) > days else rows


def _calc_delta(current, previous):
    if current is None or previous is None:
        return {'current': current, 'previous': previous, 'delta': None, 'delta_pct': None}
    delta = current - previous
    delta_pct = (delta / previous * 100.0) if previous != 0 else None
    return {'current': current, 'previous': previous, 'delta': delta, 'delta_pct': delta_pct}


def _parse_rotem_history_rows(raw_water_data):
    response_obj = raw_water_data.get('reponseObj', raw_water_data) if isinstance(raw_water_data, dict) else {}
    ds_data = response_obj.get('dsData', {}) if isinstance(response_obj, dict) else {}
    return ds_data.get('Data', []) if isinstance(ds_data, dict) else []


def _history_record_date_from_growth_day(house: House, growth_day: int, max_growth_day: int | None):
    if house.batch_start_date:
        return (house.batch_start_date + timedelta(days=growth_day)).isoformat()
    if max_growth_day is not None:
        return (timezone.localdate() - timedelta(days=(max_growth_day - growth_day))).isoformat()
    return None


def _normalize_water_feed_history(raw_water_data, house: House):
    """Reuse Rotem water parsing and enrich records with feed totals when present."""
    from rotem_scraper.views import _parse_water_history_raw

    water_rows = _parse_water_history_raw(raw_water_data, house)
    rows = _parse_rotem_history_rows(raw_water_data)
    valid_growth_days = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        try:
            growth_day = int(row.get('HistoryRecord_GrowthDay'))
        except (TypeError, ValueError):
            continue
        if growth_day >= 0:
            valid_growth_days.append(growth_day)
    max_growth_day = max(valid_growth_days) if valid_growth_days else None

    by_growth_day = {}
    by_date = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        try:
            growth_day = int(row.get('HistoryRecord_GrowthDay'))
        except (TypeError, ValueError):
            continue
        if growth_day < 0:
            continue
        record_date = _history_record_date_from_growth_day(house, growth_day, max_growth_day)
        feed = _safe_float(
            row.get('HistoryRecord_FeederTotal')
            or row.get('HistoryRecord_DailyFeed')
            or row.get('DailyFeed')
            or row.get('Feed')
        )
        water = _safe_float(
            row.get('HistoryRecord_TotalDrink')
            or row.get('HistoryRecord_TotalWater')
            or row.get('HistoryRecord_DailyWater')
            or row.get('DailyWater')
            or row.get('Water')
        )
        enriched = {
            'growth_day': growth_day,
            'date': record_date,
            'consumption_avg': water,
            'feed_consumption': feed,
        }
        by_growth_day[growth_day] = enriched
        if record_date:
            by_date[record_date] = enriched

    normalized = []
    seen_keys = set()
    for row in water_rows:
        if not isinstance(row, dict):
            continue
        growth_day = row.get('growth_day')
        date_key = row.get('date')
        raw_match = None
        if growth_day is not None:
            try:
                raw_match = by_growth_day.get(int(growth_day))
            except (TypeError, ValueError):
                raw_match = None
        if raw_match is None and date_key:
            raw_match = by_date.get(date_key)

        normalized_row = {
            **row,
            'consumption_avg': _safe_float(row.get('consumption_avg')),
            'feed_consumption': raw_match.get('feed_consumption') if raw_match else _safe_float(row.get('feed_consumption')),
        }
        key = normalized_row.get('date') or normalized_row.get('growth_day')
        if key is not None:
            seen_keys.add(str(key))
        normalized.append(normalized_row)

    for raw_row in by_growth_day.values():
        key = raw_row.get('date') or raw_row.get('growth_day')
        if key is not None and str(key) in seen_keys:
            continue
        if raw_row.get('date'):
            normalized.append(raw_row)

    normalized = [row for row in normalized if row.get('date')]
    normalized.sort(key=lambda row: row.get('date') or '')
    return normalized


def _select_history_row_for_date(rows, target_date: date | None):
    dated_rows = [row for row in rows if isinstance(row, dict) and row.get('date')]
    dated_rows.sort(key=lambda row: row.get('date') or '')
    if not dated_rows:
        return None, None

    if target_date is None:
        current = dated_rows[-1]
        previous = dated_rows[-2] if len(dated_rows) > 1 else None
        return current, previous

    target_key = target_date.isoformat()
    previous_key = (target_date - timedelta(days=1)).isoformat()
    current = next((row for row in dated_rows if row.get('date') == target_key), None)
    previous = next((row for row in dated_rows if row.get('date') == previous_key), None)
    return current, previous


def _build_water_history_comparison_row(house: House, rows, source: str, target_date: date | None, error: str | None = None):
    current, previous = _select_history_row_for_date(rows or [], target_date)
    water_current = _safe_float(current.get('consumption_avg')) if current else None
    water_previous = _safe_float(previous.get('consumption_avg')) if previous else None
    feed_current = _safe_float(current.get('feed_consumption')) if current else None
    feed_previous = _safe_float(previous.get('feed_consumption')) if previous else None
    payload = {
        'house_id': house.id,
        'house_number': house.house_number,
        'water_day_over_day': _calc_delta(water_current, water_previous),
        'feed_day_over_day': _calc_delta(feed_current, feed_previous),
        'data_quality': {
            'enough_for_dod_delta': water_current is not None and water_previous is not None,
            'has_feed_delta': feed_current is not None and feed_previous is not None,
        },
        'source': source,
    }
    if error:
        payload['error'] = error
    return payload


def _build_house_comparison_row(house: House, farm_payload: dict | None, now):
    response_obj = farm_payload.get('reponseObj', {}) if isinstance(farm_payload, dict) else {}
    live = _extract_live_house_from_site_controllers(farm_payload or {}, house.house_number) or {}
    age_days = house.age_days
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

    source_ts = live.get('source_timestamp')
    data_freshness_minutes = None
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

    return {
        'house_id': house.id,
        'house_number': house.house_number,
        'farm_id': house.farm.id,
        'farm_name': house.farm.name,
        'current_day': age_days,
        'age_days': age_days,
        'current_age_days': house.current_age_days,
        'is_integrated': house.is_integrated,
        'status': house.status,
        'is_full_house': age_days is not None and age_days >= 0,
        'last_update_time': source_ts or now,
        'average_temperature': live.get('average_temperature'),
        'outside_temperature': _safe_float(_extract_comparison_item(response_obj, 'Outside_Temperature', house.house_number)),
        'tunnel_temperature': _safe_float(_extract_comparison_item(response_obj, 'Tunnel_Temperature', house.house_number)),
        'target_temperature': _safe_float(_extract_comparison_item(response_obj, 'Set_Temperature', house.house_number)),
        'static_pressure': live.get('static_pressure'),
        'inside_humidity': live.get('humidity'),
        'ventilation_mode': _extract_comparison_item(response_obj, 'Vent_Mode', house.house_number),
        'ventilation_level': _safe_float(_extract_comparison_item(response_obj, 'Vent_Level', house.house_number)),
        'airflow_cfm': _safe_float(str(_extract_comparison_item(response_obj, 'Current_Level_CFM', house.house_number) or '').replace(',', '')),
        'airflow_percentage': live.get('airflow_percentage'),
        'water_consumption': water_consumption,
        'feed_consumption': feed_consumption,
        'water_per_bird': water_per_bird,
        'feed_per_bird': feed_per_bird,
        'water_feed_ratio': water_feed_ratio,
        'bird_count': bird_count,
        'livability': _safe_float(_extract_comparison_item(response_obj, 'Livablity_Percents', house.house_number)),
        'growth_day': age_days,
        'is_connected': bool(live.get('is_connected')),
        'has_alarms': False,
        'alarm_status': live.get('alarm_status') or 'normal',
        'active_alarms_count': None,
        'data_freshness_minutes': data_freshness_minutes,
        'heater_on': heater_on,
        'fan_on': fan_on,
        'wind_speed': _safe_float(_extract_comparison_item(response_obj, 'Wind_Speed', house.house_number)),
        'wind_direction': _safe_float(_extract_comparison_item(response_obj, 'Wind_Direction', house.house_number)),
        'wind_chill_temperature': _safe_float(_extract_comparison_item(response_obj, 'Wind_Chill_Temperature', house.house_number)),
    }


def _build_house_comparison_row_from_snapshot(house: House, snapshot, now):
    age_days = house.age_days
    water_consumption = snapshot.water_consumption if snapshot else None
    feed_consumption = snapshot.feed_consumption if snapshot else None
    bird_count = snapshot.bird_count if snapshot else None
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
    timestamp = snapshot.timestamp if snapshot else now
    return {
        'house_id': house.id,
        'house_number': house.house_number,
        'farm_id': house.farm.id,
        'farm_name': house.farm.name,
        'current_day': age_days,
        'age_days': age_days,
        'current_age_days': house.current_age_days,
        'is_integrated': house.is_integrated,
        'status': house.status,
        'is_full_house': age_days is not None and age_days >= 0,
        'last_update_time': timestamp,
        'average_temperature': snapshot.average_temperature if snapshot else None,
        'outside_temperature': snapshot.outside_temperature if snapshot else None,
        'tunnel_temperature': None,
        'target_temperature': snapshot.target_temperature if snapshot else None,
        'static_pressure': snapshot.static_pressure if snapshot else None,
        'inside_humidity': snapshot.humidity if snapshot else None,
        'ventilation_mode': None,
        'ventilation_level': snapshot.ventilation_level if snapshot else None,
        'airflow_cfm': snapshot.airflow_cfm if snapshot else None,
        'airflow_percentage': snapshot.airflow_percentage if snapshot else None,
        'water_consumption': water_consumption,
        'feed_consumption': feed_consumption,
        'water_per_bird': water_per_bird,
        'feed_per_bird': feed_per_bird,
        'water_feed_ratio': water_feed_ratio,
        'bird_count': bird_count,
        'livability': snapshot.livability if snapshot else None,
        'growth_day': age_days,
        'is_connected': bool(snapshot.is_connected) if snapshot else False,
        'has_alarms': bool(snapshot.has_alarms) if snapshot else False,
        'alarm_status': snapshot.alarm_status if snapshot else 'unknown',
        'active_alarms_count': None,
        'data_freshness_minutes': max(int((now - timestamp).total_seconds() / 60), 0) if timestamp else None,
        'heater_on': False,
        'fan_on': False,
        'wind_speed': None,
        'wind_direction': None,
        'wind_chill_temperature': None,
    }


def _comparison_payload_from_rows(rows):
    rows.sort(key=lambda row: (row['farm_name'], row['house_number']))
    serializer = HouseComparisonSerializer(rows, many=True)
    return {'count': len(serializer.data), 'houses': serializer.data}


def _db_comparison_payload(houses):
    now = timezone.now()
    rows = [
        _build_house_comparison_row_from_snapshot(house, house.get_latest_snapshot(), now)
        for house in houses
    ]
    return _comparison_payload_from_rows(rows)


def _lightweight_farm_comparison_payload(farm: Farm, houses):
    now = timezone.now()
    if not houses:
        return {'count': 0, 'houses': []}, now
    scraper, err = _house_rotem_scraper_or_error(houses[0])
    if err:
        detail = getattr(err, 'data', {}).get('detail', 'Failed to initialize Rotem scraper.')
        raise ValueError(detail)
    farm_payload = scraper.get_site_controllers_info() or {}
    if not farm_payload:
        raise ValueError('No live Rotem comparison data returned.')
    source_ts = _parse_site_controllers_source_timestamp(farm_payload) or now
    rows = [_build_house_comparison_row(house, farm_payload, now) for house in houses]
    return _comparison_payload_from_rows(rows), source_ts


def _snapshot_fallback_for_house(house: House):
    snapshot = house.get_latest_snapshot()
    if not snapshot:
        return None
    return {
        'house_id': house.id,
        'house_number': house.house_number,
        'current_day': house.age_days,
        'status': house.status,
        'active_alarms_count': 0,
        'timestamp': snapshot.timestamp.isoformat() if snapshot.timestamp else timezone.now().isoformat(),
        'source_timestamp': snapshot.timestamp.isoformat() if snapshot.timestamp else timezone.now().isoformat(),
        'average_temperature': snapshot.average_temperature,
        'humidity': snapshot.humidity,
        'static_pressure': snapshot.static_pressure,
        'airflow_percentage': snapshot.airflow_percentage,
        'water_consumption': snapshot.water_consumption,
        'feed_consumption': snapshot.feed_consumption,
        'is_connected': snapshot.is_connected if snapshot.connection_status is not None else True,
        'alarm_status': snapshot.alarm_status or 'normal',
    }


def _severity_rank(value: str) -> int:
    order = {'low': 1, 'medium': 2, 'high': 3, 'critical': 4}
    return order.get((value or '').lower(), 0)


def _build_alerts_by_house(houses):
    house_ids = [h.id for h in houses]
    if not house_ids:
        return {}
    now = timezone.now()
    qs = WaterConsumptionAlert.objects.filter(
        house_id__in=house_ids,
        is_resolved=False,
    ).filter(
        Q(snoozed_until__isnull=True) | Q(snoozed_until__lte=now)
    ).values('house_id', 'severity', 'message', 'created_at')
    grouped = defaultdict(list)
    for row in qs:
        grouped[row['house_id']].append(row)

    alerts_by_house = {}
    for house in houses:
        rows = grouped.get(house.id, [])
        highest = max(rows, key=lambda r: _severity_rank(r.get('severity') or ''), default=None)
        alerts_by_house[house.id] = {
            'active_count': len(rows),
            'highest_severity': (highest or {}).get('severity') or 'normal',
            'latest_message': (highest or {}).get('message'),
            'latest_created_at': ((highest or {}).get('created_at').isoformat() if (highest or {}).get('created_at') else None),
        }
    return alerts_by_house


def _compose_monitoring_snapshot_payload(farm: Farm, houses, dashboard_payload, houses_payload):
    houses_payload_rows = []
    if isinstance(houses_payload, dict):
        houses_payload_rows = houses_payload.get('houses') or []
    houses_by_number = {
        int(row.get('house_number')): row
        for row in houses_payload_rows
        if isinstance(row, dict) and row.get('house_number') is not None
    }

    dashboard_rows = []
    if isinstance(dashboard_payload, dict):
        dashboard_rows = dashboard_payload.get('houses') or []
    dashboard_by_number = {
        int(row.get('house_number')): row
        for row in dashboard_rows
        if isinstance(row, dict) and row.get('house_number') is not None
    }

    alerts_by_house = _build_alerts_by_house(houses)
    rows = []
    for house in houses:
        dashboard_row = dashboard_by_number.get(house.house_number, {})
        houses_row = houses_by_number.get(house.house_number, {})
        fallback_row = _snapshot_fallback_for_house(house) or {}
        alert_meta = alerts_by_house.get(house.id, {'active_count': 0, 'highest_severity': 'normal'})
        rows.append({
            'house_id': house.id,
            'house_number': house.house_number,
            'current_day': dashboard_row.get('current_day', house.age_days),
            'status': dashboard_row.get('status', house.status),
            'timestamp': dashboard_row.get('timestamp') or houses_row.get('timestamp') or fallback_row.get('timestamp'),
            'source_timestamp': dashboard_row.get('source_timestamp') or houses_row.get('source_timestamp') or fallback_row.get('source_timestamp'),
            'average_temperature': dashboard_row.get('average_temperature') or houses_row.get('average_temperature') or fallback_row.get('average_temperature'),
            'humidity': dashboard_row.get('humidity') or houses_row.get('humidity') or fallback_row.get('humidity'),
            'static_pressure': dashboard_row.get('static_pressure') or houses_row.get('static_pressure') or fallback_row.get('static_pressure'),
            'airflow_percentage': dashboard_row.get('airflow_percentage') or houses_row.get('airflow_percentage') or fallback_row.get('airflow_percentage'),
            'water_consumption': dashboard_row.get('water_consumption') or houses_row.get('water_consumption') or fallback_row.get('water_consumption'),
            'feed_consumption': dashboard_row.get('feed_consumption') or houses_row.get('feed_consumption') or fallback_row.get('feed_consumption'),
            'is_connected': bool(dashboard_row.get('is_connected', fallback_row.get('is_connected', True))),
            'alarm_status': dashboard_row.get('alarm_status') or fallback_row.get('alarm_status') or 'normal',
            'active_alarms_count': int(alert_meta.get('active_count') or 0),
        })

    connected = len([r for r in rows if r.get('is_connected')])
    snapshot = {
        'farm_id': farm.id,
        'farm_name': farm.name,
        'total_houses': len(houses),
        'houses': rows,
        'alerts_by_house': {str(k): v for k, v in alerts_by_house.items()},
        'alerts_summary': {
            'total_active': sum((v.get('active_count') or 0) for v in alerts_by_house.values()),
            'critical': len([v for v in alerts_by_house.values() if (v.get('highest_severity') or '').lower() == 'critical']),
            'warning': len([v for v in alerts_by_house.values() if (v.get('highest_severity') or '').lower() == 'warning']),
            'normal': len([v for v in alerts_by_house.values() if (v.get('active_count') or 0) == 0]),
        },
        'connection_summary': {
            'connected': connected,
            'disconnected': max(len(houses) - connected, 0),
        },
    }
    return snapshot


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
    cache = (
        _ensure_house_cache(house, 'latest_payload', force=(mode == 'live'))
        if mode != 'live'
        else HouseMonitoringCache.objects.filter(house=house).first()
    )
    if mode != 'live' and cache and cache.latest_payload:
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
    if mode != 'live':
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
    else:
        cache = None
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
    cache = (
        _ensure_house_cache(house, 'history_payload', force=(mode == 'live'))
        if mode != 'live'
        else HouseMonitoringCache.objects.filter(house=house).first()
    )
    if mode != 'live' and cache and cache.history_payload:
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

        water = _safe_float(
            row.get('HistoryRecord_TotalDrink')
            or row.get('HistoryRecord_TotalWater')
            or row.get('HistoryRecord_DailyWater')
            or row.get('DailyWater')
            or row.get('Water')
        )
        feed = _safe_float(
            row.get('HistoryRecord_FeederTotal')
            or row.get('HistoryRecord_DailyFeed')
            or row.get('DailyFeed')
            or row.get('Feed')
        )
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
    if mode != 'live':
        HouseMonitoringCache.objects.update_or_create(
            house=house,
            defaults={
                'history_payload': payload,
                'source_timestamp': timezone.now(),
                'refresh_state': 'fresh',
                'last_error': '',
            },
        )
    meta = build_meta(timezone.now(), timezone.now(), 'fresh', MAX_STALE_SECONDS)
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
    cache = (
        _ensure_house_cache(house, 'kpis_payload', force=(mode == 'live'))
        if mode != 'live'
        else HouseMonitoringCache.objects.filter(house=house).first()
    )
    if mode != 'live' and cache and cache.kpis_payload:
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
        w = _safe_float(
            row.get('HistoryRecord_TotalDrink')
            or row.get('HistoryRecord_TotalWater')
            or row.get('HistoryRecord_DailyWater')
            or row.get('DailyWater')
            or row.get('Water')
        )
        f = _safe_float(
            row.get('HistoryRecord_FeederTotal')
            or row.get('HistoryRecord_DailyFeed')
            or row.get('DailyFeed')
            or row.get('Feed')
        )
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

    heater_hours_24h = None
    heater_cycles_24h = None

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
            'method': 'not_loaded_one_rotem_call_limit',
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
    if mode != 'live':
        HouseMonitoringCache.objects.update_or_create(
            house=house,
            defaults={
                'kpis_payload': payload,
                'source_timestamp': timezone.now(),
                'refresh_state': 'fresh',
                'last_error': '',
            },
        )
    meta = build_meta(timezone.now(), timezone.now(), 'fresh', MAX_STALE_SECONDS)
    return Response(wrap_cached_response(payload, meta))


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def farm_houses_monitoring_all(request, farm_id):
    """Get latest monitoring for all houses in a farm (cached-first by default)."""
    farm = get_object_or_404(_scoped_farms_queryset(request), id=farm_id)
    mode = _cache_mode(request)
    cache = (
        _ensure_farm_cache(farm, force=(mode == 'live'))
        if mode != 'live'
        else FarmMonitoringCache.objects.filter(farm=farm).first()
    )
    if mode != 'live' and cache and cache.houses_payload:
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
    if mode != 'live':
        FarmMonitoringCache.objects.update_or_create(
            farm=farm,
            defaults={
                'houses_payload': payload,
                'source_timestamp': timezone.now(),
                'refresh_state': 'fresh',
                'last_error': '',
            },
        )
    meta = build_meta(timezone.now(), timezone.now(), 'fresh', MAX_STALE_SECONDS)
    return Response(wrap_cached_response(payload, meta))


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def farm_houses_monitoring_dashboard(request, farm_id):
    """Get dashboard data (cached-first by default)."""
    farm = get_object_or_404(_scoped_farms_queryset(request), id=farm_id)
    mode = _cache_mode(request)
    cache = (
        _ensure_farm_cache(farm, force=(mode == 'live'))
        if mode != 'live'
        else FarmMonitoringCache.objects.filter(farm=farm).first()
    )
    if mode != 'live' and cache and cache.dashboard_payload:
        meta = build_meta(cache.fetched_at, cache.source_timestamp, cache.refresh_state, MAX_STALE_SECONDS)
        payload = cache.dashboard_payload
        if isinstance(payload, dict) and not payload.get('houses'):
            houses = list(House.objects.filter(farm=farm, is_active=True).order_by('house_number'))
            fallback_houses = []
            for house in houses:
                row = _snapshot_fallback_for_house(house)
                if row:
                    fallback_houses.append(row)
            if fallback_houses:
                payload = {
                    'farm_id': farm_id,
                    'farm_name': farm.name,
                    'total_houses': len(houses),
                    'houses': fallback_houses,
                    'alerts_summary': {'total_active': 0, 'critical': 0, 'warning': 0, 'normal': len(fallback_houses)},
                    'connection_summary': {'connected': len(fallback_houses), 'disconnected': 0},
                }
        return Response(wrap_cached_response(payload, meta))

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

    if mode != 'live':
        FarmMonitoringCache.objects.update_or_create(
            farm=farm,
            defaults={
                'dashboard_payload': dashboard_data,
                'source_timestamp': timezone.now(),
                'refresh_state': 'fresh',
                'last_error': '',
            },
        )
    meta = build_meta(timezone.now(), timezone.now(), 'fresh', MAX_STALE_SECONDS)
    return Response(wrap_cached_response(dashboard_data, meta))


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def farm_houses_monitoring_snapshot(request, farm_id):
    """Get one cached-first monitoring snapshot for all houses in a farm."""
    farm = get_object_or_404(_scoped_farms_queryset(request), id=farm_id)
    mode = _cache_mode(request)
    cache = (
        _ensure_farm_cache(farm, force=(mode == 'live'))
        if mode != 'live'
        else FarmMonitoringCache.objects.filter(farm=farm).first()
    )
    houses = list(House.objects.filter(farm=farm, is_active=True).order_by('house_number'))

    if mode != 'live' and cache and (cache.dashboard_payload or cache.houses_payload):
        snapshot = _compose_monitoring_snapshot_payload(
            farm=farm,
            houses=houses,
            dashboard_payload=cache.dashboard_payload or {},
            houses_payload=cache.houses_payload or {},
        )
        meta = build_meta(cache.fetched_at, cache.source_timestamp, cache.refresh_state, MAX_STALE_SECONDS)
        return Response(wrap_cached_response(snapshot, meta))

    if not houses:
        snapshot = {
            'farm_id': farm.id,
            'farm_name': farm.name,
            'total_houses': 0,
            'houses': [],
            'alerts_by_house': {},
            'alerts_summary': {'total_active': 0, 'critical': 0, 'warning': 0, 'normal': 0},
            'connection_summary': {'connected': 0, 'disconnected': 0},
        }
        return Response(wrap_cached_response(snapshot, build_meta(timezone.now(), timezone.now(), 'fresh', MAX_STALE_SECONDS)))

    dashboard_payload = {}
    houses_payload = {}
    if mode != 'cached':
        scraper, err = _house_rotem_scraper_or_error(houses[0])
        if not err:
            site_payload = scraper.get_site_controllers_info() or {}
            live_rows = []
            dashboard_rows = []
            for house in houses:
                live = _extract_live_house_from_site_controllers(site_payload, house.house_number)
                if not live:
                    continue
                live_rows.append({
                    'house_id': house.id,
                    'house_number': house.house_number,
                    'timestamp': live.get('timestamp'),
                    'source_timestamp': live.get('source_timestamp'),
                    'average_temperature': live.get('average_temperature'),
                    'humidity': live.get('humidity'),
                    'static_pressure': live.get('static_pressure'),
                    'airflow_percentage': live.get('airflow_percentage'),
                    'water_consumption': live.get('water_consumption'),
                    'feed_consumption': live.get('feed_consumption'),
                    'is_connected': bool(live.get('is_connected')),
                    'alarm_status': live.get('alarm_status') or 'normal',
                })
                dashboard_rows.append({
                    'house_id': house.id,
                    'house_number': house.house_number,
                    'current_day': house.age_days,
                    'status': house.status,
                    'timestamp': live.get('timestamp'),
                    'source_timestamp': live.get('source_timestamp'),
                    'average_temperature': live.get('average_temperature'),
                    'humidity': live.get('humidity'),
                    'static_pressure': live.get('static_pressure'),
                    'airflow_percentage': live.get('airflow_percentage'),
                    'water_consumption': live.get('water_consumption'),
                    'feed_consumption': live.get('feed_consumption'),
                    'is_connected': bool(live.get('is_connected')),
                    'alarm_status': live.get('alarm_status') or 'normal',
                    'active_alarms_count': 0,
                })
            houses_payload = {'houses': live_rows}
            dashboard_payload = {'houses': dashboard_rows}

    if mode != 'live' and not dashboard_payload and cache and cache.dashboard_payload:
        dashboard_payload = cache.dashboard_payload
    if mode != 'live' and not houses_payload and cache and cache.houses_payload:
        houses_payload = cache.houses_payload

    snapshot = _compose_monitoring_snapshot_payload(
        farm=farm,
        houses=houses,
        dashboard_payload=dashboard_payload,
        houses_payload=houses_payload,
    )
    refresh_state = 'fresh' if (dashboard_payload or houses_payload) else 'failed'
    source_ts = timezone.now()
    if mode != 'live' and cache and cache.source_timestamp:
        source_ts = cache.source_timestamp
    elif snapshot.get('houses'):
        source_raw = snapshot['houses'][0].get('source_timestamp')
        if isinstance(source_raw, str):
            try:
                source_ts = datetime.fromisoformat(source_raw.replace('Z', '+00:00'))
            except ValueError:
                source_ts = timezone.now()
    meta = build_meta(
        fetched_at=timezone.now(),
        source_timestamp=source_ts,
        refresh_state=refresh_state,
        stale_seconds=MAX_STALE_SECONDS,
    )
    return Response(wrap_cached_response(snapshot, meta))


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
    cache = (
        _ensure_house_cache(house, 'heater_payload', force=(mode == 'live'))
        if mode != 'live'
        else HouseMonitoringCache.objects.filter(house=house).first()
    )
    if mode != 'live' and cache and cache.heater_payload:
        meta = build_meta(cache.fetched_at, cache.source_timestamp, cache.refresh_state, MAX_STALE_SECONDS)
        return Response(wrap_cached_response(cache.heater_payload, meta))

    scraper, err = _house_rotem_scraper_or_error(house)
    if err:
        return err

    parsed = scraper.get_heater_history(house_number=house.house_number) or {}
    records = parsed.get('records', []) if isinstance(parsed, dict) else []

    # Pre-compute max growth_day for relative-date fallback when batch_start_date is None.
    valid_growth_days = []
    for r in records:
        gd = r.get('growth_day')
        if gd is not None:
            try:
                valid_growth_days.append(int(gd))
            except (TypeError, ValueError):
                pass
    max_growth_day = max(valid_growth_days) if valid_growth_days else 0
    today = timezone.localdate()

    daily = []
    for r in records:
        growth_day = r.get('growth_day')
        if growth_day is None:
            continue
        try:
            growth_day = int(growth_day)
        except (TypeError, ValueError):
            continue
        dt = None
        if house.batch_start_date:
            try:
                dt = house.batch_start_date + timedelta(days=growth_day)
            except (TypeError, ValueError):
                dt = None
        if dt is None and growth_day >= 0:
            dt = today - timedelta(days=(max_growth_day - growth_day))
        daily.append({
            'growth_day': growth_day,
            'date': dt.isoformat() if dt else None,
            'total_hours': _safe_float(r.get('total_runtime_hours')) or 0.0,
            'total_minutes': int(r.get('total_runtime_minutes') or 0),
            'device_breakdown': r.get('per_device', {}),
        })
    daily.sort(key=lambda row: row.get('growth_day', 0))
    payload = {'heater_history': {'daily': daily}}
    if mode != 'live':
        HouseMonitoringCache.objects.update_or_create(
            house=house,
            defaults={
                'heater_payload': payload,
                'source_timestamp': timezone.now(),
                'refresh_state': 'fresh',
                'last_error': '',
            },
        )
    meta = build_meta(timezone.now(), timezone.now(), 'fresh', MAX_STALE_SECONDS)
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
    """Get houses comparison data without triggering the full monitoring refresh path."""
    farm_id = request.query_params.get('farm_id')
    mode = _cache_mode(request)
    house_ids = request.query_params.getlist('house_ids')

    if farm_id:
        scoped_farm = get_object_or_404(_scoped_farms_queryset(request), id=farm_id)
        cache = FarmMonitoringCache.objects.filter(farm=scoped_farm).first()
        if mode != 'live' and cache and cache.comparison_payload:
            meta = build_meta(cache.fetched_at, cache.source_timestamp, cache.refresh_state, MAX_STALE_SECONDS)
            return Response(wrap_cached_response(cache.comparison_payload, meta))

        houses = list(
            _scoped_houses_queryset(request)
            .filter(farm=scoped_farm, is_active=True)
            .select_related('farm')
            .order_by('farm__name', 'house_number')
        )
        if house_ids:
            house_id_set = {int(house_id) for house_id in house_ids if str(house_id).isdigit()}
            houses = [house for house in houses if house.id in house_id_set]

        if mode == 'cached':
            payload = _db_comparison_payload(houses)
            meta = build_meta(
                cache.fetched_at if cache else timezone.now(),
                cache.source_timestamp if cache else timezone.now(),
                cache.refresh_state if cache else 'idle',
                MAX_STALE_SECONDS,
            )
            meta['source'] = 'db_fallback'
            return Response(wrap_cached_response(payload, meta))

        try:
            payload, source_ts = _lightweight_farm_comparison_payload(scoped_farm, houses)
            cache, _ = FarmMonitoringCache.objects.update_or_create(
                farm=scoped_farm,
                defaults={
                    'comparison_payload': payload,
                    'source_timestamp': source_ts,
                    'refresh_state': 'fresh',
                    'last_error': '',
                },
            )
            meta = build_meta(cache.fetched_at, cache.source_timestamp, cache.refresh_state, MAX_STALE_SECONDS)
            meta['source'] = 'live'
            return Response(wrap_cached_response(payload, meta))
        except Exception as exc:
            if cache and cache.comparison_payload:
                meta = build_meta(cache.fetched_at, cache.source_timestamp, cache.refresh_state, MAX_STALE_SECONDS)
                meta['warning'] = str(exc)
                meta['source'] = 'stale_cache'
                return Response(wrap_cached_response(cache.comparison_payload, meta))
            payload = _db_comparison_payload(houses)
            meta = build_meta(timezone.now(), timezone.now(), 'failed', MAX_STALE_SECONDS)
            meta['warning'] = str(exc)
            meta['source'] = 'db_fallback'
            return Response(wrap_cached_response(payload, meta))

    houses = list(
        _scoped_houses_queryset(request)
        .filter(is_active=True)
        .select_related('farm')
        .order_by('farm__name', 'house_number')
    )
    if house_ids:
        house_id_set = {int(house_id) for house_id in house_ids if str(house_id).isdigit()}
        houses = [house for house in houses if house.id in house_id_set]

    if mode != 'live':
        payload = _db_comparison_payload(houses)
        meta = build_meta(timezone.now(), timezone.now(), 'idle', MAX_STALE_SECONDS)
        meta['source'] = 'db_fallback'
        return Response(wrap_cached_response(payload, meta))

    rows = []
    warnings = []
    farms_by_id = {}
    houses_by_farm_id = {}
    for house in houses:
        farms_by_id[house.farm_id] = house.farm
        houses_by_farm_id.setdefault(house.farm_id, []).append(house)

    for farm_id_value, farm in farms_by_id.items():
        farm_houses = houses_by_farm_id[farm_id_value]
        try:
            payload, source_ts = _lightweight_farm_comparison_payload(farm, farm_houses)
            FarmMonitoringCache.objects.update_or_create(
                farm=farm,
                defaults={
                    'comparison_payload': payload,
                    'source_timestamp': source_ts,
                    'refresh_state': 'fresh',
                    'last_error': '',
                },
            )
            rows.extend(payload.get('houses', []))
        except Exception as exc:
            warnings.append(f'{farm.id}: {exc}')
            now = timezone.now()
            rows.extend([
                _build_house_comparison_row_from_snapshot(house, house.get_latest_snapshot(), now)
                for house in farm_houses
            ])
    payload = _comparison_payload_from_rows(rows)
    meta = build_meta(timezone.now(), timezone.now(), 'fresh' if not warnings else 'failed', MAX_STALE_SECONDS)
    if warnings:
        meta['warning'] = '; '.join(warnings)
    meta['source'] = 'live' if not warnings else 'partial_db_fallback'
    return Response(wrap_cached_response(payload, meta))


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def farm_comparison_refresh(request, farm_id):
    """Refresh only the farm comparison payload without building per-house monitoring caches."""
    farm = get_object_or_404(_scoped_farms_queryset(request), id=farm_id, is_active=True)
    houses = list(
        _scoped_houses_queryset(request)
        .filter(farm=farm, is_active=True)
        .select_related('farm')
        .order_by('farm__name', 'house_number')
    )
    cache = FarmMonitoringCache.objects.filter(farm=farm).first()
    try:
        payload, source_ts = _lightweight_farm_comparison_payload(farm, houses)
        cache, _ = FarmMonitoringCache.objects.update_or_create(
            farm=farm,
            defaults={
                'comparison_payload': payload,
                'source_timestamp': source_ts,
                'refresh_state': 'fresh',
                'last_error': '',
            },
        )
        meta = build_meta(cache.fetched_at, cache.source_timestamp, cache.refresh_state, MAX_STALE_SECONDS)
        meta['source'] = 'live'
        return Response(wrap_cached_response(payload, meta))
    except Exception as exc:
        if cache and cache.comparison_payload:
            meta = build_meta(cache.fetched_at, cache.source_timestamp, cache.refresh_state, MAX_STALE_SECONDS)
            meta['warning'] = str(exc)
            meta['source'] = 'stale_cache'
            return Response(wrap_cached_response(cache.comparison_payload, meta))
        payload = _db_comparison_payload(houses)
        meta = build_meta(timezone.now(), timezone.now(), 'failed', MAX_STALE_SECONDS)
        meta['warning'] = str(exc)
        meta['source'] = 'db_fallback'
        return Response(wrap_cached_response(payload, meta))


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def farm_water_history_comparison(request, farm_id):
    """Get per-house water/feed day-over-day comparison from cached or parallel Rotem history."""
    farm = get_object_or_404(_scoped_farms_queryset(request), id=farm_id, is_active=True)
    mode = _cache_mode(request)
    days = _parse_int_query_param(request.query_params.get('days'), default=8, minimum=1, maximum=30)
    ref_date_raw = request.query_params.get('dod_reference_date')
    ref_date = None
    if ref_date_raw:
        try:
            ref_date = date.fromisoformat(ref_date_raw)
        except ValueError:
            return Response(
                {'detail': 'dod_reference_date must be YYYY-MM-DD.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

    houses = list(
        _scoped_houses_queryset(request)
        .filter(farm=farm, is_active=True)
        .order_by('house_number')
    )
    now = timezone.now()
    caches = {
        cache.house_id: cache
        for cache in HouseMonitoringCache.objects.filter(house__in=houses)
    }
    response_houses = {}
    stale_houses = []

    for house in houses:
        cache = caches.get(house.id)
        has_payload = bool(cache and cache.water_history_payload)
        is_fresh = bool(
            cache
            and cache.water_history_fetched_at
            and (now - cache.water_history_fetched_at).total_seconds() < MAX_STALE_SECONDS
        )
        if mode != 'live' and has_payload and (is_fresh or mode == 'cached'):
            source = 'cache' if is_fresh else 'stale_cache'
            rows = _trim_history_rows(cache.water_history_payload, days)
            response_houses[str(house.id)] = _build_water_history_comparison_row(house, rows, source, ref_date)
        elif mode == 'cached':
            response_houses[str(house.id)] = _build_water_history_comparison_row(
                house,
                [],
                'failed',
                ref_date,
                error='No cached water history is available for this house.',
            )
        else:
            stale_houses.append(house)

    def fetch_house_history(house: House):
        if not farm.rotem_username or not farm.rotem_password:
            raise ValueError('Farm Rotem credentials are not configured.')
        scraper = RotemScraper(username=farm.rotem_username, password=farm.rotem_password)
        if not scraper.login():
            raise ValueError('Failed to authenticate with Rotem API.')
        raw = scraper.get_water_history(house_number=house.house_number) or {}
        rows = _normalize_water_feed_history(raw, house)
        HouseMonitoringCache.objects.update_or_create(
            house=house,
            defaults={
                'water_history_payload': rows,
                'water_history_fetched_at': timezone.now(),
                'source_timestamp': timezone.now(),
                'refresh_state': 'fresh',
                'last_error': '',
            },
        )
        return rows

    if stale_houses:
        max_workers = min(4, len(stale_houses))
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(fetch_house_history, house): house for house in stale_houses}
            for future in as_completed(futures):
                house = futures[future]
                cache = caches.get(house.id)
                try:
                    rows = future.result()
                    response_houses[str(house.id)] = _build_water_history_comparison_row(
                        house,
                        _trim_history_rows(rows, days),
                        'live',
                        ref_date,
                    )
                except Exception as exc:
                    logger.warning(
                        'farm_water_history_comparison_failed farm=%s house=%s err=%s',
                        farm.id,
                        house.house_number,
                        exc,
                    )
                    if cache and cache.water_history_payload:
                        response_houses[str(house.id)] = _build_water_history_comparison_row(
                            house,
                            _trim_history_rows(cache.water_history_payload, days),
                            'stale_cache',
                            ref_date,
                            error=str(exc),
                        )
                    else:
                        response_houses[str(house.id)] = _build_water_history_comparison_row(
                            house,
                            [],
                            'failed',
                            ref_date,
                            error=str(exc),
                        )

    ordered_houses = {
        str(house.id): response_houses[str(house.id)]
        for house in houses
        if str(house.id) in response_houses
    }
    partial = any(row.get('source') == 'failed' or row.get('error') for row in ordered_houses.values())
    return Response({
        'farm_id': farm.id,
        'days': days,
        'dod_reference_date': ref_date.isoformat() if ref_date else None,
        'houses': ordered_houses,
        'meta': {
            'fetched_at': timezone.now().isoformat(),
            'partial': partial,
        },
    })


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


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def farm_ios_snapshot(request, farm_id):
    """
    Unified iOS snapshot: all monitoring data the iOS app needs in one
    cache-consistent response. All fields come from the same scrape cycle,
    eliminating the inconsistency caused by merging three separate endpoints.

    Returns farm-level metadata, per-house freshness statuses, and a complete
    houses array with every sensor field.
    """
    farm = get_object_or_404(_scoped_farms_queryset(request), id=farm_id)
    mode = _cache_mode(request)
    if mode == 'live':
        houses = list(House.objects.filter(farm=farm, is_active=True).order_by('house_number'))
        if not houses:
            meta = build_meta(timezone.now(), timezone.now(), 'fresh', MAX_STALE_SECONDS)
            return Response(wrap_cached_response({
                "farm_id": farm.id,
                "farm_name": farm.name,
                "total_houses": 0,
                "houses": [],
                "alerts_summary": {"total_active": 0, "critical": 0, "warning": 0, "normal": 0},
                "alerts_by_house": {},
                "connection_summary": {"connected": 0, "disconnected": 0},
            }, meta))

        scraper, err = _house_rotem_scraper_or_error(houses[0])
        if err:
            return err
        site_payload = scraper.get_site_controllers_info() or {}
        source_ts = _parse_site_controllers_source_timestamp(site_payload) or timezone.now()
        houses_data = []
        house_statuses = {}
        connection_summary = {"connected": 0, "disconnected": 0}
        alerts_summary = {"total_active": 0, "critical": 0, "warning": 0, "normal": 0}

        for house in houses:
            live = _extract_live_house_from_site_controllers(site_payload, house.house_number)
            if not live:
                house_statuses[str(house.house_number)] = {
                    "status": "failed",
                    "source_timestamp": None,
                    "error_msg": "no_live_data",
                }
                houses_data.append({
                    "house_id": house.id,
                    "house_number": house.house_number,
                    "current_day": house.age_days,
                    "status": house.status,
                    "is_connected": False,
                    "alarm_status": "normal",
                    "active_alarms_count": 0,
                    "data_status": "failed",
                })
                connection_summary["disconnected"] += 1
                alerts_summary["normal"] += 1
                continue

            house_statuses[str(house.house_number)] = {
                "status": "ok",
                "source_timestamp": live.get("source_timestamp"),
                "error_msg": None,
            }
            is_connected = bool(live.get("is_connected"))
            if is_connected:
                connection_summary["connected"] += 1
            else:
                connection_summary["disconnected"] += 1
            alarm_status = live.get("alarm_status") or "normal"
            if alarm_status == "critical":
                alerts_summary["critical"] += 1
            elif alarm_status == "warning":
                alerts_summary["warning"] += 1
            else:
                alerts_summary["normal"] += 1
            houses_data.append({
                "house_id": house.id,
                "house_number": house.house_number,
                "timestamp": live.get("timestamp"),
                "source_timestamp": live.get("source_timestamp"),
                "average_temperature": live.get("average_temperature"),
                "humidity": live.get("humidity"),
                "static_pressure": live.get("static_pressure"),
                "airflow_percentage": live.get("airflow_percentage"),
                "water_consumption": live.get("water_consumption"),
                "feed_consumption": live.get("feed_consumption"),
                "current_day": house.age_days,
                "growth_day": house.age_days,
                "status": house.status,
                "is_connected": is_connected,
                "alarm_status": alarm_status,
                "active_alarms_count": 0,
                "data_status": "ok",
            })

        alerts_by_house = {}
        try:
            active_alerts = WaterConsumptionAlert.objects.filter(
                farm=farm,
                is_resolved=False,
            ).select_related("house")
            for alert in active_alerts:
                house_id = alert.house_id
                if house_id not in alerts_by_house:
                    alerts_by_house[str(house_id)] = {
                        "active_count": 0,
                        "highest_severity": "low",
                        "latest_message": None,
                    }
                entry = alerts_by_house[str(house_id)]
                entry["active_count"] += 1
                severity_rank = {"low": 0, "medium": 1, "high": 2, "critical": 3}
                if severity_rank.get(alert.severity, 0) > severity_rank.get(entry["highest_severity"], 0):
                    entry["highest_severity"] = alert.severity
                if entry["latest_message"] is None:
                    entry["latest_message"] = getattr(alert, "message", None) or f"Water alert ({alert.severity})"
        except Exception:
            pass
        alerts_summary["total_active"] = sum(v.get("active_count", 0) for v in alerts_by_house.values())

        meta = build_meta(
            fetched_at=timezone.now(),
            source_timestamp=source_ts,
            refresh_state='fresh',
            stale_seconds=MAX_STALE_SECONDS,
            house_statuses=house_statuses,
            circuit_open=False,
        )
        return Response(wrap_cached_response({
            "farm_id": farm.id,
            "farm_name": farm.name,
            "total_houses": len(houses),
            "houses": houses_data,
            "alerts_summary": alerts_summary,
            "alerts_by_house": alerts_by_house,
            "connection_summary": connection_summary,
        }, meta))

    cache = _ensure_farm_cache(farm)

    now = timezone.now()
    circuit_open = bool(
        cache and cache.last_error == "circuit_open" and cache.refresh_state == "failed"
    )

    # Build per-house list from cache
    houses_data = []
    if cache and isinstance(cache.houses_payload, dict):
        for h in cache.houses_payload.get("houses", []):
            if isinstance(h, dict):
                houses_data.append(h)

    # For any active house missing from cache, fall back to latest DB snapshot
    if cache:
        cached_house_numbers = {h.get("house_number") for h in houses_data if isinstance(h, dict)}
        db_houses = House.objects.filter(farm=farm, is_active=True).exclude(
            house_number__in=cached_house_numbers
        )
        for house in db_houses:
            snap = (
                HouseMonitoringSnapshot.objects
                .filter(house=house)
                .order_by("-timestamp")
                .first()
            )
            if snap:
                houses_data.append({
                    "house_id": house.id,
                    "house_number": house.house_number,
                    "timestamp": snap.timestamp.isoformat(),
                    "source_timestamp": snap.timestamp.isoformat(),
                    "average_temperature": float(snap.average_temperature) if snap.average_temperature is not None else None,
                    "humidity": float(snap.humidity) if snap.humidity is not None else None,
                    "static_pressure": float(snap.static_pressure) if snap.static_pressure is not None else None,
                    "airflow_percentage": float(snap.ventilation_level) if snap.ventilation_level is not None else None,
                    "water_consumption": float(snap.water_consumption) if snap.water_consumption is not None else None,
                    "feed_consumption": float(snap.feed_consumption) if snap.feed_consumption is not None else None,
                    "current_day": house.age_days,
                    "status": house.status,
                    "is_connected": snap.connection_status == 1,
                    "alarm_status": snap.alarm_status or "normal",
                    "active_alarms_count": 0,
                    "data_status": "db_fallback",
                })

    source_ts = cache.source_timestamp if cache else None
    fetched_at = cache.fetched_at if cache else now
    refresh_state = cache.refresh_state if cache else "idle"
    house_statuses = (cache.house_statuses or {}) if cache else {}

    meta = build_meta(
        fetched_at=fetched_at,
        source_timestamp=source_ts,
        refresh_state=refresh_state,
        stale_seconds=MAX_STALE_SECONDS,
        house_statuses=house_statuses,
        circuit_open=circuit_open,
    )

    dashboard = (cache.dashboard_payload or {}) if cache else {}
    alerts_summary = dashboard.get("alerts_summary", {
        "total_active": 0, "critical": 0, "warning": 0, "normal": 0,
    })
    connection_summary = dashboard.get("connection_summary", {
        "connected": 0, "disconnected": 0,
    })

    # Per-house alert details (for iOS alarm mapping)
    alerts_by_house = {}
    try:
        active_alerts = WaterConsumptionAlert.objects.filter(
            farm=farm,
            is_resolved=False,
        ).select_related("house")
        for alert in active_alerts:
            house_id = alert.house_id
            if house_id not in alerts_by_house:
                alerts_by_house[str(house_id)] = {
                    "active_count": 0,
                    "highest_severity": "low",
                    "latest_message": None,
                }
            entry = alerts_by_house[str(house_id)]
            entry["active_count"] += 1
            severity_rank = {"low": 0, "medium": 1, "high": 2, "critical": 3}
            if severity_rank.get(alert.severity, 0) > severity_rank.get(entry["highest_severity"], 0):
                entry["highest_severity"] = alert.severity
            if entry["latest_message"] is None:
                entry["latest_message"] = getattr(alert, "message", None) or f"Water alert ({alert.severity})"
    except Exception:
        pass

    data = {
        "farm_id": farm.id,
        "farm_name": farm.name,
        "total_houses": House.objects.filter(farm=farm, is_active=True).count(),
        "houses": sorted(houses_data, key=lambda h: h.get("house_number", 0) if isinstance(h, dict) else 0),
        "alerts_summary": alerts_summary,
        "alerts_by_house": alerts_by_house,
        "connection_summary": connection_summary,
    }

    return Response(wrap_cached_response(data, meta))


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def farm_data_quality(request, farm_id):
    """Snapshot completeness and staleness metrics per house."""
    from .services.data_quality_service import DataQualityService

    get_object_or_404(Farm, id=farm_id)
    days = int(request.query_params.get('days', 1))
    service = DataQualityService()
    return Response(service.farm_metrics(farm_id, days=days))


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def house_monitoring_trends(request, house_id):
    """
    Daily trend series for water, feed, and temperature.
    Optional compare_growth_day=N overlays prior flock at same growth day.
    """
    house = get_object_or_404(House, id=house_id)
    period = int(request.query_params.get('period', 14))
    compare_gd = request.query_params.get('compare_growth_day')

    end = timezone.now().date()
    start = end - timedelta(days=period)
    current_series = list(
        HouseDailySummary.objects.filter(house=house, date__gte=start, date__lte=end).order_by('date')
    )

    comparison_series = []
    if compare_gd is not None:
        try:
            gd = int(compare_gd)
        except ValueError:
            gd = None
        if gd is not None:
            comparison_series = list(
                HouseDailySummary.objects.filter(house=house, growth_day=gd)
                .order_by('-date')[:period]
            )
            comparison_series = sorted(comparison_series, key=lambda s: s.date)

    return Response({
        'house_id': house.id,
        'house_number': house.house_number,
        'period_days': period,
        'current_series': HouseDailySummarySerializer(current_series, many=True).data,
        'comparison_growth_day': int(compare_gd) if compare_gd is not None else None,
        'comparison_series': HouseDailySummarySerializer(comparison_series, many=True).data,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def house_flock_risk_scores(request, house_id):
    """Latest ML risk scores for active flocks in a house."""
    house = get_object_or_404(House, id=house_id)
    risk_type = request.query_params.get('risk_type', 'mortality_3d')
    latest = []
    seen = set()
    for s in (
        FlockRiskScore.objects.filter(house=house, risk_type=risk_type)
        .select_related('flock')
        .order_by('-scored_at')
    ):
        if s.flock_id not in seen:
            seen.add(s.flock_id)
            latest.append(s)
    return Response({
        'house_id': house.id,
        'risk_scores': FlockRiskScoreSerializer(latest, many=True).data,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def farm_data_quality(request, farm_id):
    """Snapshot completeness and staleness metrics per house."""
    from .services.data_quality_service import DataQualityService

    get_object_or_404(Farm, id=farm_id)
    days = int(request.query_params.get('days', 1))
    service = DataQualityService()
    return Response(service.farm_metrics(farm_id, days=days))


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def house_monitoring_trends(request, house_id):
    """
    Daily trend series for water, feed, and temperature.
    Optional compare_growth_day=N overlays prior flock at same growth day.
    """
    house = get_object_or_404(House, id=house_id)
    period = int(request.query_params.get('period', 14))
    compare_gd = request.query_params.get('compare_growth_day')

    end = timezone.now().date()
    start = end - timedelta(days=period)
    current_series = list(
        HouseDailySummary.objects.filter(house=house, date__gte=start, date__lte=end).order_by('date')
    )

    comparison_series = []
    if compare_gd is not None:
        try:
            gd = int(compare_gd)
        except ValueError:
            gd = None
        if gd is not None:
            comparison_series = list(
                HouseDailySummary.objects.filter(house=house, growth_day=gd)
                .order_by('-date')[:period]
            )
            comparison_series = sorted(comparison_series, key=lambda s: s.date)

    return Response({
        'house_id': house.id,
        'house_number': house.house_number,
        'period_days': period,
        'current_series': HouseDailySummarySerializer(current_series, many=True).data,
        'comparison_growth_day': int(compare_gd) if compare_gd is not None else None,
        'comparison_series': HouseDailySummarySerializer(comparison_series, many=True).data,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def house_flock_risk_scores(request, house_id):
    """Latest ML risk scores for active flocks in a house."""
    house = get_object_or_404(House, id=house_id)
    risk_type = request.query_params.get('risk_type', 'mortality_3d')
    scores = (
        FlockRiskScore.objects.filter(house=house, risk_type=risk_type)
        .select_related('flock')
        .order_by('flock', '-scored_at')
        .distinct('flock')
    )
    # SQLite may not support distinct on fields; fallback for tests
    try:
        data = FlockRiskScoreSerializer(scores, many=True).data
    except Exception:
        seen = set()
        latest = []
        for s in FlockRiskScore.objects.filter(house=house, risk_type=risk_type).select_related('flock').order_by('-scored_at'):
            if s.flock_id not in seen:
                seen.add(s.flock_id)
                latest.append(s)
        data = FlockRiskScoreSerializer(latest, many=True).data
    return Response({'house_id': house.id, 'risk_scores': data})
