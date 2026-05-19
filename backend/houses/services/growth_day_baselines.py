"""Growth-day-aware baselines for consumption and environment detectors."""
from __future__ import annotations

from statistics import mean, stdev
from typing import Dict, List, Optional, Tuple

from django.db.models import Avg

from houses.models import House, HouseDailySummary, HouseMonitoringSnapshot


def get_house_growth_day(house: House) -> int:
    latest = house.monitoring_snapshots.order_by('-timestamp').first()
    if latest and latest.growth_day is not None:
        return int(latest.growth_day)
    return house.age_days or 0


def daily_summaries_for_growth_day(
    house: House,
    growth_day: int,
    limit: int = 14,
    exclude_date=None,
) -> List[HouseDailySummary]:
    qs = HouseDailySummary.objects.filter(house=house, growth_day=growth_day)
    if exclude_date:
        qs = qs.exclude(date=exclude_date)
    return list(qs.order_by('-date')[:limit])


def baseline_from_daily_summaries(
    summaries: List[HouseDailySummary],
    field: str,
) -> Optional[Tuple[float, float]]:
    """Return (mean, std) for a numeric field on daily summaries."""
    values = [
        float(getattr(s, field))
        for s in summaries
        if getattr(s, field, None) is not None
    ]
    if len(values) < 2:
        if len(values) == 1:
            return values[0], values[0] * 0.1
        return None
    m = mean(values)
    sd = stdev(values) if len(values) > 1 else m * 0.1
    return m, max(sd, m * 0.05)


def snapshot_baseline_same_growth_day(
    house: House,
    growth_day: int,
    field: str,
    hours: int = 168,
) -> Optional[float]:
    """Fallback: average snapshot field for same growth_day in lookback window."""
    from django.utils import timezone
    from datetime import timedelta

    since = timezone.now() - timedelta(hours=hours)
    agg = HouseMonitoringSnapshot.objects.filter(
        house=house,
        growth_day=growth_day,
        timestamp__gte=since,
    ).aggregate(avg=Avg(field))
    val = agg.get('avg')
    return float(val) if val is not None else None


def target_temperature_for_growth_day(house: House, growth_day: int) -> Optional[float]:
    """Read target from ControlSettings temperature curve if configured."""
    try:
        settings_obj = house.control_settings
    except Exception:
        return None
    curve = list(settings_obj.temperature_curves.order_by('day'))
    if not curve:
        return settings_obj.target_temperature
    best = min(curve, key=lambda c: abs(c.day - growth_day))
    return float(best.target_temperature)
