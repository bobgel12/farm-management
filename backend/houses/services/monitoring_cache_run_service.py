from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional
import os
import uuid

from django.db import connections, transaction
from django.utils import timezone

from farms.models import Farm
from houses.models import FarmMonitoringCache, MonitoringCacheRefreshRun
from houses.services.monitoring_cache_service import (
    MAX_STALE_SECONDS,
    build_meta,
    upsert_farm_monitoring_cache,
)


TERMINAL_STATUSES = {"success", "partial", "failed"}
ACTIVE_STATUSES = {"queued", "running"}


def _run_result(run: MonitoringCacheRefreshRun) -> dict:
    return {
        "run_id": str(run.run_id),
        "trigger_type": run.trigger_type,
        "status": run.status,
        "started_at": run.started_at.isoformat() if run.started_at else None,
        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
        "farms_processed": run.farms_processed,
        "houses_processed": run.houses_processed,
        "result_payload": run.result_payload or {},
        "error_summary": run.error_summary,
        "created_at": run.created_at.isoformat() if run.created_at else None,
        "updated_at": run.updated_at.isoformat() if run.updated_at else None,
    }


def serialize_refresh_run(run: Optional[MonitoringCacheRefreshRun]) -> Optional[dict]:
    if not run:
        return None
    return _run_result(run)


def queue_manual_refresh_run(requested_by=None) -> MonitoringCacheRefreshRun:
    active = (
        MonitoringCacheRefreshRun.objects.filter(trigger_type="manual", status__in=ACTIVE_STATUSES)
        .order_by("-created_at")
        .first()
    )
    if active:
        return active
    return MonitoringCacheRefreshRun.objects.create(
        run_id=uuid.uuid4(),
        trigger_type="manual",
        status="queued",
        requested_by=requested_by if getattr(requested_by, "is_authenticated", False) else None,
    )


def create_scheduled_refresh_run() -> MonitoringCacheRefreshRun:
    return MonitoringCacheRefreshRun.objects.create(
        run_id=uuid.uuid4(),
        trigger_type="scheduled",
        status="running",
        started_at=timezone.now(),
    )


def claim_next_queued_manual_run() -> Optional[MonitoringCacheRefreshRun]:
    with transaction.atomic():
        run = (
            MonitoringCacheRefreshRun.objects.select_for_update()
            .filter(trigger_type="manual", status="queued")
            .order_by("created_at")
            .first()
        )
        if not run:
            return None
        run.status = "running"
        run.started_at = timezone.now()
        run.save(update_fields=["status", "started_at", "updated_at"])
        return run


def _refresh_one_farm(farm_id: int) -> dict:
    try:
        farm = Farm.objects.get(id=farm_id)
        result = upsert_farm_monitoring_cache(farm)
        cache = FarmMonitoringCache.objects.filter(farm=farm).first()
        return {
            "farm_id": farm.id,
            "farm_name": farm.name,
            "status": result.status,
            "message": result.message,
            "houses_processed": result.houses_processed,
            "cache_fetched_at": cache.fetched_at.isoformat() if cache else None,
            "cache_source_timestamp": cache.source_timestamp.isoformat() if cache and cache.source_timestamp else None,
        }
    except Exception as exc:
        return {
            "farm_id": farm_id,
            "status": "failed",
            "message": str(exc),
            "houses_processed": 0,
        }
    finally:
        connections.close_all()


def execute_refresh_run(run: MonitoringCacheRefreshRun) -> MonitoringCacheRefreshRun:
    if run.status != "running":
        run.status = "running"
        run.started_at = run.started_at or timezone.now()
        run.save(update_fields=["status", "started_at", "updated_at"])

    farm_ids = list(
        Farm.objects.filter(
            is_active=True,
            has_system_integration=True,
            integration_type="rotem",
        ).values_list("id", flat=True)
    )
    max_workers = max(1, int(os.getenv("MONITORING_CACHE_REFRESH_MAX_WORKERS", "4")))
    max_workers = min(max_workers, max(len(farm_ids), 1))

    farm_results = []
    if farm_ids:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(_refresh_one_farm, farm_id) for farm_id in farm_ids]
            for future in as_completed(futures):
                farm_results.append(future.result())

    successes = [row for row in farm_results if row.get("status") == "success"]
    failures = [row for row in farm_results if row.get("status") != "success"]
    if not farm_results:
        final_status = "success"
    elif failures and successes:
        final_status = "partial"
    elif failures:
        final_status = "failed"
    else:
        final_status = "success"

    run.status = final_status
    run.completed_at = timezone.now()
    run.farms_processed = len(successes)
    run.houses_processed = sum(int(row.get("houses_processed") or 0) for row in farm_results)
    run.result_payload = {
        "farm_count": len(farm_ids),
        "max_workers": max_workers,
        "farms": sorted(farm_results, key=lambda row: row.get("farm_id") or 0),
    }
    run.error_summary = "; ".join(
        f"farm={row.get('farm_id')}:{row.get('message') or row.get('status')}" for row in failures
    )
    run.save()
    connections.close_all()
    return run


def latest_runs() -> dict:
    return {
        "scheduled": serialize_refresh_run(
            MonitoringCacheRefreshRun.objects.filter(trigger_type="scheduled").order_by("-created_at").first()
        ),
        "manual": serialize_refresh_run(
            MonitoringCacheRefreshRun.objects.filter(trigger_type="manual").order_by("-created_at").first()
        ),
    }


def farm_cache_status_payload(farm: Farm, interval_seconds: int = 600) -> dict:
    cache = FarmMonitoringCache.objects.filter(farm=farm).first()
    fetched_at = cache.fetched_at if cache else None
    source_timestamp = cache.source_timestamp if cache else None
    refresh_state = cache.refresh_state if cache else "missing"
    meta = build_meta(fetched_at, source_timestamp, refresh_state, MAX_STALE_SECONDS)
    return {
        "farm_id": farm.id,
        "farm_name": farm.name,
        "cache": {
            "exists": bool(cache),
            "fetched_at": fetched_at.isoformat() if fetched_at else None,
            "source_timestamp": source_timestamp.isoformat() if source_timestamp else None,
            "age_seconds": meta.get("age_seconds"),
            "is_stale": meta.get("is_stale"),
            "refresh_state": refresh_state,
            "last_error": cache.last_error if cache else "",
        },
        "worker_interval_seconds": interval_seconds,
        "latest_runs": latest_runs(),
    }
