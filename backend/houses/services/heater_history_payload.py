"""Serialize cached CommandID 43 heater history for API responses."""
from __future__ import annotations

from django.utils import timezone

from rotem_scraper.models import HouseHeaterRuntimeCache


def build_heater_history_payload(house) -> dict:
    """Build heater_history dict from DB cache only (no Rotem calls)."""
    heater_cache_rows = list(
        HouseHeaterRuntimeCache.objects.filter(house=house).order_by("growth_day")
    )
    now = timezone.now()
    cache_last_synced_at = max(
        (row.last_synced_at for row in heater_cache_rows),
        default=None,
    )
    cache_stale_after_minutes = 30
    is_stale = True
    if cache_last_synced_at:
        is_stale = (now - cache_last_synced_at).total_seconds() > (
            cache_stale_after_minutes * 60
        )

    sync_status = "fresh"
    if not heater_cache_rows:
        sync_status = "missing"
    elif is_stale:
        sync_status = "stale"

    summary_row = next((row for row in heater_cache_rows if row.is_summary_row), None)
    daily_rows = [row for row in heater_cache_rows if not row.is_summary_row]

    def _format_per_device(per_device_json):
        if not isinstance(per_device_json, dict):
            return {}
        out = {}
        for key, value in per_device_json.items():
            if isinstance(value, dict):
                minutes = int(value.get("minutes") or 0)
                out[key] = {
                    "minutes": minutes,
                    "hours": round(minutes / 60.0, 2),
                    "raw_value": value.get("raw_value"),
                }
            else:
                minutes = int(value or 0)
                out[key] = {
                    "minutes": minutes,
                    "hours": round(minutes / 60.0, 2),
                    "raw_value": None,
                }
        return out

    daily_payload = []
    for row in daily_rows:
        daily_payload.append(
            {
                "growth_day": row.growth_day,
                "date": row.record_date.isoformat() if row.record_date else None,
                "total_minutes": row.total_runtime_minutes,
                "total_hours": round(row.total_runtime_minutes / 60.0, 2),
                "total_computation_method": row.total_computation_method,
                "per_device": _format_per_device(row.per_device_json),
                "last_synced_at": row.last_synced_at.isoformat()
                if row.last_synced_at
                else None,
            }
        )

    summary_minutes = sum(item["total_minutes"] for item in daily_payload)
    device_keys = set()
    for item in daily_payload:
        device_keys.update(item["per_device"].keys())

    return {
        "summary": {
            "total_minutes": summary_minutes,
            "total_hours": round(summary_minutes / 60.0, 2),
            "days_count": len(daily_payload),
            "device_count": len(device_keys),
            "summary_row_minutes": summary_row.total_runtime_minutes
            if summary_row
            else None,
            "summary_row_hours": round(summary_row.total_runtime_minutes / 60.0, 2)
            if summary_row
            else None,
        },
        "daily": daily_payload,
        "latest": daily_payload[-1] if daily_payload else None,
        "freshness": {
            "last_synced_at": cache_last_synced_at.isoformat()
            if cache_last_synced_at
            else None,
            "stale": is_stale if heater_cache_rows else True,
            "sync_status": sync_status,
            "stale_after_minutes": cache_stale_after_minutes,
        },
    }
