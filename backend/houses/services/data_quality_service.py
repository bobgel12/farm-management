"""Data completeness and freshness metrics for Rotem monitoring snapshots."""
from __future__ import annotations

from datetime import timedelta
from typing import Any, Dict, List, Optional

from django.conf import settings
from django.utils import timezone

from houses.models import House, HouseMonitoringSnapshot


class DataQualityService:
    """Compute snapshot completeness and staleness per house or farm."""

    def __init__(self, interval_seconds: Optional[int] = None):
        self.interval_seconds = interval_seconds or getattr(
            settings, 'MONITORING_SNAPSHOT_INTERVAL_SECONDS', 300
        )

    def expected_snapshots_per_day(self) -> int:
        return max(1, int(86400 / self.interval_seconds))

    def house_metrics(self, house: House, days: int = 1) -> Dict[str, Any]:
        end = timezone.now()
        start = end - timedelta(days=days)
        snapshots = HouseMonitoringSnapshot.objects.filter(
            house=house,
            timestamp__gte=start,
            timestamp__lte=end,
        )
        count = snapshots.count()
        expected = self.expected_snapshots_per_day() * days
        completeness = min(1.0, count / expected) if expected else 0.0

        latest = snapshots.order_by('-timestamp').first()
        last_age_minutes = None
        if latest:
            last_age_minutes = (end - latest.timestamp).total_seconds() / 60.0

        stale = last_age_minutes is None or last_age_minutes > (self.interval_seconds / 60.0) * 2

        return {
            'house_id': house.id,
            'house_number': house.house_number,
            'farm_id': house.farm_id,
            'period_days': days,
            'snapshot_count': count,
            'expected_snapshots': expected,
            'completeness_ratio': round(completeness, 4),
            'completeness_percent': round(completeness * 100, 1),
            'meets_target': completeness >= 0.95,
            'last_snapshot_at': latest.timestamp.isoformat() if latest else None,
            'last_snapshot_age_minutes': round(last_age_minutes, 1) if last_age_minutes is not None else None,
            'is_stale': stale,
            'connection_ok': bool(latest and latest.connection_status == 1),
        }

    def farm_metrics(self, farm_id: int, days: int = 1) -> Dict[str, Any]:
        houses = House.objects.filter(farm_id=farm_id, is_active=True).order_by('house_number')
        house_rows: List[Dict[str, Any]] = []
        ratios: List[float] = []

        for house in houses:
            m = self.house_metrics(house, days=days)
            house_rows.append(m)
            ratios.append(m['completeness_ratio'])

        avg_completeness = sum(ratios) / len(ratios) if ratios else 0.0
        return {
            'farm_id': farm_id,
            'period_days': days,
            'houses': house_rows,
            'house_count': len(house_rows),
            'avg_completeness_ratio': round(avg_completeness, 4),
            'avg_completeness_percent': round(avg_completeness * 100, 1),
            'meets_target': avg_completeness >= 0.95,
            'stale_house_count': sum(1 for h in house_rows if h['is_stale']),
        }
