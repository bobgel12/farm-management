from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from django.db import transaction
from django.utils import timezone
import logging

from farms.models import Farm
from houses.models import House, FarmMonitoringCache, HouseMonitoringCache
from rotem_scraper.scraper import RotemScraper


MAX_STALE_SECONDS = 600
CIRCUIT_OPEN_THRESHOLD = 5
logger = logging.getLogger(__name__)

# Module-level Redis client (lazy-initialised, None if Redis unavailable)
_redis_client = None


def _get_redis():
    global _redis_client
    if _redis_client is None:
        try:
            import redis as redis_lib
            from django.conf import settings
            _redis_client = redis_lib.from_url(settings.CELERY_BROKER_URL, socket_connect_timeout=2)
        except Exception as exc:
            logger.warning("redis_unavailable lock_disabled err=%s", exc)
            _redis_client = False  # sentinel: don't retry
    return _redis_client if _redis_client else None


def safe_float(value):
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def parse_source_timestamp(payload: dict) -> Optional[datetime]:
    if not isinstance(payload, dict):
        return None
    response_obj = payload.get("reponseObj")
    if not isinstance(response_obj, dict):
        return None
    raw = response_obj.get("LastUpdateDT")
    if not isinstance(raw, str):
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None


def extract_current_numeric(house_data: dict, key: str):
    section = house_data.get(key, {}) if isinstance(house_data, dict) else {}
    if not isinstance(section, dict):
        return None
    return safe_float(section.get("CurrentNumericValue"))


def extract_live_house(payload: dict, house_number: int):
    response_obj = payload.get("reponseObj") if isinstance(payload, dict) else None
    farm_houses = response_obj.get("FarmHouses", []) if isinstance(response_obj, dict) else []
    target = None
    for row in farm_houses:
        if isinstance(row, dict) and int(row.get("HouseNumber", -1)) == int(house_number):
            target = row
            break
    if not target:
        return None
    data = target.get("Data", {}) if isinstance(target.get("Data"), dict) else {}
    source_ts = parse_source_timestamp(payload) or timezone.now()
    return {
        "house_id": int(target.get("HouseNumber", house_number)),
        "source_timestamp": source_ts.isoformat(),
        "timestamp": timezone.now().isoformat(),
        "average_temperature": extract_current_numeric(data, "Temperature"),
        "humidity": extract_current_numeric(data, "Humidity"),
        "static_pressure": extract_current_numeric(data, "Pressure"),
        "airflow_percentage": extract_current_numeric(data, "VentLevel"),
        "water_consumption": extract_current_numeric(data, "DailyWater"),
        "feed_consumption": extract_current_numeric(data, "DailyFeed"),
        "is_connected": int(target.get("ConnectionStatus", 0)) == 1,
        "alarm_status": "normal",
    }


def extract_comparison_item(response_obj: dict, category: str, house_number: int):
    if not isinstance(response_obj, dict):
        return None
    dic = response_obj.get("DicComparisonItems", {})
    if not isinstance(dic, dict):
        return None
    bucket = dic.get(category, {})
    if not isinstance(bucket, dict):
        return None
    return bucket.get(f"House{house_number}")


def build_meta(
    fetched_at: Optional[datetime],
    source_timestamp: Optional[datetime],
    refresh_state: str,
    stale_seconds: int = MAX_STALE_SECONDS,
    house_statuses: Optional[Dict] = None,
    circuit_open: bool = False,
):
    now = timezone.now()
    source = source_timestamp or fetched_at
    age_seconds = None
    if source:
        age_seconds = max(int((now - source).total_seconds()), 0)
    is_stale = age_seconds is None or age_seconds > stale_seconds
    meta = {
        "source_timestamp": source.isoformat() if source else None,
        "fetched_at": fetched_at.isoformat() if fetched_at else None,
        "age_seconds": age_seconds,
        "is_stale": is_stale,
        "refresh_state": refresh_state,
        "can_refresh_now": True,
        "circuit_open": circuit_open,
    }
    if house_statuses is not None:
        meta["house_statuses"] = house_statuses
    return meta


def wrap_cached_response(data: Any, meta: Dict[str, Any]):
    return {"data": data, "meta": meta}


@dataclass
class UpsertResult:
    status: str
    message: str = ""
    farms_processed: int = 0
    houses_processed: int = 0


def _farm_scraper(farm: Farm) -> Optional[RotemScraper]:
    if not farm.rotem_username or not farm.rotem_password:
        return None
    scraper = RotemScraper(username=farm.rotem_username, password=farm.rotem_password)
    if not scraper.login():
        return None
    return scraper


def _build_house_history(house: House, scraper: RotemScraper, limit: int = 100):
    now = timezone.now()
    start_dt = now - timedelta(days=5)
    raw_water = scraper.get_water_history(
        house_number=house.house_number,
        start_date=start_dt.date().isoformat(),
        end_date=now.date().isoformat(),
    ) or {}
    response_obj = raw_water.get("reponseObj", raw_water) if isinstance(raw_water, dict) else {}
    ds_data = response_obj.get("dsData", {}) if isinstance(response_obj, dict) else {}
    rows = ds_data.get("Data", []) if isinstance(ds_data, dict) else []
    results = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        growth_day = row.get("HistoryRecord_GrowthDay") or row.get("HistoryRecord_Heaters_GrowthDay")
        date_str = row.get("HistoryRecord_Date")
        source_ts = None
        if isinstance(date_str, str):
            try:
                source_ts = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            except ValueError:
                source_ts = None
        if source_ts is None and growth_day is not None and house.batch_start_date:
            try:
                source_ts = datetime.combine(
                    house.batch_start_date + timedelta(days=int(growth_day)),
                    datetime.min.time(),
                    tzinfo=timezone.get_current_timezone(),
                )
            except (TypeError, ValueError):
                source_ts = timezone.now()
        if source_ts is None:
            source_ts = timezone.now()
        results.append(
            {
                "source_timestamp": source_ts.isoformat(),
                "timestamp": timezone.now().isoformat(),
                "average_temperature": None,
                "humidity": None,
                "static_pressure": None,
                "airflow_percentage": None,
                "water_consumption": safe_float(row.get("HistoryRecord_DailyWater") or row.get("DailyWater") or row.get("Water")),
                "feed_consumption": safe_float(row.get("HistoryRecord_DailyFeed") or row.get("DailyFeed") or row.get("Feed")),
            }
        )
    site_payload = scraper.get_site_controllers_info() or {}
    live = extract_live_house(site_payload, house.house_number)
    if live:
        results.append(live)
    return {
        "count": len(results[-limit:]),
        "start_date": start_dt.isoformat(),
        "end_date": now.isoformat(),
        "results": sorted(results, key=lambda x: x.get("source_timestamp") or x.get("timestamp"))[-limit:],
    }


def _build_house_kpis(house: House, scraper: RotemScraper):
    now = timezone.now()
    start_date = (now.date() - timedelta(days=7)).isoformat()
    end_date = now.date().isoformat()
    raw_water = scraper.get_water_history(house_number=house.house_number, start_date=start_date, end_date=end_date) or {}
    response_obj = raw_water.get("reponseObj", raw_water) if isinstance(raw_water, dict) else {}
    ds_data = response_obj.get("dsData", {}) if isinstance(response_obj, dict) else {}
    rows = ds_data.get("Data", []) if isinstance(ds_data, dict) else []
    water_by_day = {}
    feed_by_day = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        gday = row.get("HistoryRecord_GrowthDay")
        try:
            gday = int(gday)
        except (TypeError, ValueError):
            continue
        day_key = str(gday)
        if house.batch_start_date:
            day_key = (house.batch_start_date + timedelta(days=gday)).isoformat()
        w = safe_float(row.get("HistoryRecord_DailyWater") or row.get("DailyWater") or row.get("Water"))
        f = safe_float(row.get("HistoryRecord_DailyFeed") or row.get("DailyFeed") or row.get("Feed"))
        if w is not None:
            water_by_day[day_key] = w
        if f is not None:
            feed_by_day[day_key] = f

    def calc_delta(current, previous):
        if current is None or previous is None:
            return {"current": current, "previous": previous, "delta": None, "delta_pct": None}
        delta = current - previous
        delta_pct = (delta / previous * 100.0) if previous != 0 else None
        return {"current": current, "previous": previous, "delta": delta, "delta_pct": delta_pct}

    sorted_water_days = sorted(water_by_day.keys())
    sorted_feed_days = sorted(feed_by_day.keys())
    water_today = water_by_day.get(sorted_water_days[-1]) if sorted_water_days else None
    water_yesterday = water_by_day.get(sorted_water_days[-2]) if len(sorted_water_days) > 1 else None
    feed_today = feed_by_day.get(sorted_feed_days[-1]) if sorted_feed_days else None
    feed_yesterday = feed_by_day.get(sorted_feed_days[-2]) if len(sorted_feed_days) > 1 else None

    heater_data = scraper.get_heater_history(house_number=house.house_number) or {}
    heater_records = heater_data.get("records", []) if isinstance(heater_data, dict) else []
    heater_hours_24h = None
    heater_cycles_24h = None
    if heater_records:
        last = heater_records[-1]
        heater_hours_24h = safe_float(last.get("total_runtime_hours"))
        per_device = last.get("per_device", {}) if isinstance(last.get("per_device"), dict) else {}
        heater_cycles_24h = len(
            [k for k, v in per_device.items() if isinstance(v, dict) and (v.get("minutes") or 0) > 0]
        )

    ratio_today = (water_today / feed_today) if (water_today is not None and feed_today not in [None, 0]) else None
    ratio_yesterday = (
        (water_yesterday / feed_yesterday) if (water_yesterday is not None and feed_yesterday not in [None, 0]) else None
    )
    ratio_delta_pct = (
        ((ratio_today - ratio_yesterday) / ratio_yesterday * 100.0)
        if (ratio_today is not None and ratio_yesterday not in [None, 0])
        else None
    )
    return {
        "house_id": house.id,
        "window_hours": 24,
        "heater_runtime": {
            "hours_24h": heater_hours_24h,
            "cycles_24h": heater_cycles_24h,
            "method": "rotem_command_43_live",
        },
        "water_day_over_day": calc_delta(water_today, water_yesterday),
        "feed_day_over_day": calc_delta(feed_today, feed_yesterday),
        "water_feed_ratio": {"today": ratio_today, "yesterday": ratio_yesterday, "delta_pct": ratio_delta_pct},
    }


def _build_house_heater_payload(house: House, scraper: RotemScraper):
    parsed = scraper.get_heater_history(house_number=house.house_number) or {}
    records = parsed.get("records", []) if isinstance(parsed, dict) else []
    daily = []
    for r in records:
        growth_day = r.get("growth_day")
        if growth_day is None:
            continue
        dt = None
        if house.batch_start_date:
            try:
                dt = house.batch_start_date + timedelta(days=int(growth_day))
            except (TypeError, ValueError):
                dt = None
        daily.append(
            {
                "growth_day": int(growth_day),
                "date": dt.isoformat() if dt else None,
                "total_hours": safe_float(r.get("total_runtime_hours")) or 0.0,
                "total_minutes": int(r.get("total_runtime_minutes") or 0),
                "device_breakdown": r.get("per_device", {}),
            }
        )
    daily.sort(key=lambda row: row.get("growth_day", 0))
    return {"heater_history": {"daily": daily}}


def _build_house_cache_payloads(house: House, scraper: RotemScraper, live: dict, source_ts: datetime) -> dict:
    """Build all per-house cache payloads in memory (does NOT write to DB)."""
    history_payload = _build_house_history(house, scraper)
    kpis_payload = _build_house_kpis(house, scraper)
    heater_payload = _build_house_heater_payload(house, scraper)
    return {
        "latest_payload": live,
        "history_payload": history_payload,
        "kpis_payload": kpis_payload,
        "heater_payload": heater_payload,
        "source_timestamp": source_ts,
        "refresh_state": "fresh",
        "last_error": "",
    }


def _is_circuit_open(farm: Farm) -> bool:
    try:
        from integrations.models import IntegrationHealth
        health = IntegrationHealth.objects.filter(farm=farm, integration_type="rotem").first()
        return health is not None and health.consecutive_failures >= CIRCUIT_OPEN_THRESHOLD
    except Exception:
        return False


def upsert_farm_monitoring_cache(farm: Farm) -> UpsertResult:
    started = timezone.now()

    # --- Distributed lock (prevents concurrent scrapes for same farm) ---
    lock = None
    r = _get_redis()
    if r:
        try:
            lock = r.lock(f"scrape_lock:farm:{farm.id}", timeout=240, blocking_timeout=5)
            if not lock.acquire(blocking=True):
                logger.info("scrape_lock_skipped farm=%s reason=lock_not_acquired", farm.id)
                return UpsertResult(status="skipped", message="lock_not_acquired")
        except Exception as exc:
            logger.warning("scrape_lock_error farm=%s err=%s proceeding_without_lock", farm.id, exc)
            lock = None

    try:
        return _upsert_farm_monitoring_cache_inner(farm, started)
    finally:
        if lock:
            try:
                lock.release()
            except Exception:
                pass


def _upsert_farm_monitoring_cache_inner(farm: Farm, started: datetime) -> UpsertResult:
    # --- Circuit breaker ---
    if _is_circuit_open(farm):
        logger.warning("circuit_open farm=%s serving_cache", farm.id)
        FarmMonitoringCache.objects.filter(farm=farm).update(
            refresh_state="failed", last_error="circuit_open"
        )
        return UpsertResult(status="circuit_open", message="circuit_open")

    # --- Login ---
    scraper = _farm_scraper(farm)
    if not scraper:
        FarmMonitoringCache.objects.update_or_create(
            farm=farm,
            defaults={"refresh_state": "failed", "last_error": "Failed to authenticate with Rotem API."},
        )
        return UpsertResult(status="error", message="login_failed")

    site_payload = scraper.get_site_controllers_info()
    if not site_payload:
        FarmMonitoringCache.objects.update_or_create(
            farm=farm,
            defaults={"refresh_state": "failed", "last_error": "No live data returned from Rotem."},
        )
        return UpsertResult(status="error", message="empty_site_controllers")

    houses = list(House.objects.filter(farm=farm, is_active=True).order_by("house_number"))

    # --- Phase 1: Collect all house live data in memory ---
    house_live: Dict[int, Optional[dict]] = {}  # house.id -> live dict or None
    for house in houses:
        house_live[house.id] = extract_live_house(site_payload, house.house_number)

    failed_house_numbers = {
        h.house_number for h in houses if house_live[h.id] is None
    }

    # --- Phase 2: Per-house retry for partial failures ---
    if 0 < len(failed_house_numbers) <= 4:
        logger.warning(
            "scrape_partial_failure farm=%s failed_houses=%s retrying",
            farm.id, sorted(failed_house_numbers),
        )
        retry_scraper = _farm_scraper(farm)
        if retry_scraper:
            retry_site = retry_scraper.get_site_controllers_info() or {}
            for house in houses:
                if house.house_number in failed_house_numbers:
                    live = extract_live_house(retry_site, house.house_number)
                    if live:
                        house_live[house.id] = live
                        failed_house_numbers.discard(house.house_number)
            if failed_house_numbers:
                logger.warning(
                    "retry_still_failing farm=%s houses=%s",
                    farm.id, sorted(failed_house_numbers),
                )

    # Load existing house_statuses to carry forward stale timestamps
    existing_cache = FarmMonitoringCache.objects.filter(farm=farm).first()
    prev_house_statuses: dict = (existing_cache.house_statuses or {}) if existing_cache else {}

    # --- Build house_statuses and in-memory payloads ---
    source_ts = parse_source_timestamp(site_payload) or timezone.now()
    response_obj = site_payload.get("reponseObj", {}) if isinstance(site_payload, dict) else {}

    houses_all_payload = []
    dashboard_houses = []
    comparison_houses = []
    house_cache_payloads: Dict[int, dict] = {}  # house.id -> HouseMonitoringCache defaults
    house_statuses: Dict[str, dict] = {}
    alerts_summary = {"total_active": 0, "critical": 0, "warning": 0, "normal": 0}
    connection_summary = {"connected": 0, "disconnected": 0}

    for house in houses:
        live = house_live[house.id]
        hn = str(house.house_number)

        if live is None:
            # Mark as failed or stale (carry previous timestamp if available)
            prev = prev_house_statuses.get(hn, {})
            prev_ts = prev.get("source_timestamp")
            prev_status = prev.get("status")
            house_statuses[hn] = {
                "status": "stale" if prev_status == "ok" else "failed",
                "source_timestamp": prev_ts,
                "error_msg": "no_live_data",
            }
            # Still include in dashboard/houses payloads using previous data if available
            prev_latest = None
            if existing_cache and isinstance(existing_cache.houses_payload, dict):
                prev_houses = existing_cache.houses_payload.get("houses", [])
                for ph in prev_houses:
                    if isinstance(ph, dict) and ph.get("house_number") == house.house_number:
                        prev_latest = ph
                        break
            if prev_latest:
                houses_all_payload.append(prev_latest)
                dashboard_houses.append({
                    "house_id": house.id,
                    "house_number": house.house_number,
                    "current_day": house.age_days,
                    "status": house.status,
                    "active_alarms_count": 0,
                    "timestamp": prev_latest.get("timestamp"),
                    "source_timestamp": prev_latest.get("source_timestamp"),
                    "average_temperature": prev_latest.get("average_temperature"),
                    "humidity": prev_latest.get("humidity"),
                    "static_pressure": prev_latest.get("static_pressure"),
                    "airflow_percentage": prev_latest.get("airflow_percentage"),
                    "water_consumption": prev_latest.get("water_consumption"),
                    "feed_consumption": prev_latest.get("feed_consumption"),
                    "is_connected": prev_latest.get("is_connected", False),
                    "alarm_status": prev_latest.get("alarm_status", "normal"),
                    "data_status": "stale",
                })
            continue

        # House has fresh live data
        house_statuses[hn] = {
            "status": "ok",
            "source_timestamp": live.get("source_timestamp"),
            "error_msg": None,
        }

        alarm_status = live.get("alarm_status") or "normal"
        is_connected = bool(live.get("is_connected"))

        houses_all_payload.append({
            "house_id": house.id,
            "house_number": house.house_number,
            "timestamp": live.get("timestamp"),
            "source_timestamp": live.get("source_timestamp"),
            "average_temperature": live.get("average_temperature"),
            "outside_temperature": None,
            "humidity": live.get("humidity"),
            "static_pressure": live.get("static_pressure"),
            "target_temperature": None,
            "ventilation_level": live.get("airflow_percentage"),
            "growth_day": house.age_days,
            "bird_count": None,
            "livability": None,
            "water_consumption": live.get("water_consumption"),
            "feed_consumption": live.get("feed_consumption"),
            "airflow_cfm": None,
            "airflow_percentage": live.get("airflow_percentage"),
            "connection_status": "connected" if is_connected else "disconnected",
            "alarm_status": alarm_status,
            "has_alarms": False,
            "is_connected": is_connected,
            "data_status": "ok",
        })

        dashboard_houses.append({
            "house_id": house.id,
            "house_number": house.house_number,
            "current_day": house.age_days,
            "status": house.status,
            "active_alarms_count": 0,
            "timestamp": live.get("timestamp"),
            "source_timestamp": live.get("source_timestamp"),
            "average_temperature": live.get("average_temperature"),
            "humidity": live.get("humidity"),
            "static_pressure": live.get("static_pressure"),
            "airflow_percentage": live.get("airflow_percentage"),
            "water_consumption": live.get("water_consumption"),
            "feed_consumption": live.get("feed_consumption"),
            "is_connected": is_connected,
            "alarm_status": alarm_status,
            "data_status": "ok",
        })

        if is_connected:
            connection_summary["connected"] += 1
        else:
            connection_summary["disconnected"] += 1
        if alarm_status == "critical":
            alerts_summary["critical"] += 1
        elif alarm_status == "warning":
            alerts_summary["warning"] += 1
        else:
            alerts_summary["normal"] += 1

        comparison_houses.append({
            "house_id": house.id,
            "house_number": house.house_number,
            "farm_id": house.farm.id,
            "farm_name": house.farm.name,
            "current_day": house.age_days,
            "age_days": house.age_days,
            "current_age_days": house.current_age_days,
            "is_integrated": house.is_integrated,
            "status": house.status,
            "is_full_house": house.age_days is not None and house.age_days >= 0,
            "last_update_time": live.get("source_timestamp") or timezone.now().isoformat(),
            "average_temperature": live.get("average_temperature"),
            "outside_temperature": safe_float(
                extract_comparison_item(response_obj, "Outside_Temperature", house.house_number)
            ),
            "tunnel_temperature": safe_float(
                extract_comparison_item(response_obj, "Tunnel_Temperature", house.house_number)
            ),
            "target_temperature": safe_float(
                extract_comparison_item(response_obj, "Set_Temperature", house.house_number)
            ),
            "static_pressure": live.get("static_pressure"),
            "inside_humidity": live.get("humidity"),
            "ventilation_mode": extract_comparison_item(response_obj, "Vent_Mode", house.house_number),
            "ventilation_level": safe_float(
                extract_comparison_item(response_obj, "Vent_Level", house.house_number)
            ),
            "airflow_cfm": safe_float(
                str(extract_comparison_item(response_obj, "Current_Level_CFM", house.house_number) or "").replace(",", "")
            ),
            "airflow_percentage": live.get("airflow_percentage"),
            "water_consumption": safe_float(
                extract_comparison_item(response_obj, "Water_Daily", house.house_number)
            ) or live.get("water_consumption"),
            "feed_consumption": safe_float(
                extract_comparison_item(response_obj, "Feed_Daily", house.house_number)
            ) or live.get("feed_consumption"),
            "bird_count": safe_float(
                extract_comparison_item(response_obj, "Current_Birds_Count_In_House", house.house_number)
            ),
            "is_connected": is_connected,
            "has_alarms": False,
            "alarm_status": alarm_status,
            "active_alarms_count": None,
        })

        # Build per-house cache payloads in memory (expensive Rotem calls, outside the DB transaction)
        try:
            house_cache_payloads[house.id] = _build_house_cache_payloads(house, scraper, live, source_ts)
        except Exception as exc:
            logger.warning("house_payload_build_failed farm=%s house=%s err=%s", farm.id, house.house_number, exc)
            house_cache_payloads[house.id] = {
                "latest_payload": live,
                "history_payload": {},
                "kpis_payload": {},
                "heater_payload": {},
                "source_timestamp": source_ts,
                "refresh_state": "fresh",
                "last_error": str(exc),
            }

    alerts_summary["total_active"] = alerts_summary["critical"] + alerts_summary["warning"]
    houses_processed = sum(1 for h in houses if house_live[h.id] is not None)

    # --- Phase 3: Atomic commit ---
    farm_cache_defaults = {
        "dashboard_payload": {
            "farm_id": farm.id,
            "farm_name": farm.name,
            "total_houses": len(houses),
            "houses": dashboard_houses,
            "alerts_summary": alerts_summary,
            "connection_summary": connection_summary,
        },
        "comparison_payload": {"count": len(comparison_houses), "houses": comparison_houses},
        "houses_payload": {
            "farm_id": farm.id,
            "farm_name": farm.name,
            "houses_count": len(houses_all_payload),
            "houses": houses_all_payload,
        },
        "house_statuses": house_statuses,
        "source_timestamp": source_ts,
        "refresh_state": "fresh",
        "last_error": "",
    }

    with transaction.atomic():
        # Lock the farm cache row to prevent concurrent writers
        locked_cache = FarmMonitoringCache.objects.select_for_update().filter(farm=farm).first()
        if locked_cache:
            for k, v in farm_cache_defaults.items():
                setattr(locked_cache, k, v)
            locked_cache.save()
        else:
            FarmMonitoringCache.objects.create(farm=farm, **farm_cache_defaults)

        # Write all per-house caches atomically
        for house in houses:
            if house.id in house_cache_payloads:
                HouseMonitoringCache.objects.update_or_create(
                    house=house,
                    defaults=house_cache_payloads[house.id],
                )

    elapsed_ms = int((timezone.now() - started).total_seconds() * 1000)
    logger.info(
        "monitoring_cache_upsert farm=%s status=success houses_ok=%s houses_failed=%s elapsed_ms=%s",
        farm.id, houses_processed, len(failed_house_numbers), elapsed_ms,
    )
    return UpsertResult(status="success", farms_processed=1, houses_processed=houses_processed)


def upsert_monitoring_cache_for_all_farms() -> UpsertResult:
    started = timezone.now()
    farms = Farm.objects.filter(is_active=True, has_system_integration=True, integration_type="rotem")
    processed = 0
    houses_processed = 0
    failures: List[str] = []
    for farm in farms:
        result = upsert_farm_monitoring_cache(farm)
        if result.status == "success":
            processed += 1
            houses_processed += result.houses_processed
        else:
            failures.append(f"farm={farm.id}:{result.message}")
    status = "success" if not failures else ("partial" if processed else "error")
    result = UpsertResult(
        status=status,
        message=";".join(failures),
        farms_processed=processed,
        houses_processed=houses_processed,
    )
    elapsed_ms = int((timezone.now() - started).total_seconds() * 1000)
    logger.info(
        "monitoring_cache_batch status=%s farms_processed=%s houses_processed=%s elapsed_ms=%s failures=%s",
        result.status, result.farms_processed, result.houses_processed, elapsed_ms, len(failures),
    )
    return result
