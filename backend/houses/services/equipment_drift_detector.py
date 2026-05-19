"""Equipment degradation detection via change-point style z-scores."""
from __future__ import annotations

from statistics import mean, stdev
from typing import Dict, List, Optional

from django.utils import timezone
from datetime import timedelta

from houses.models import House, HouseDailySummary
from rotem_scraper.models import HouseHeaterRuntimeCache


class EquipmentDriftDetector:
    """Detect heater runtime drift vs prior growth-day windows."""

    DRIFT_Z_THRESHOLD = 2.0

    def __init__(self, house: House):
        self.house = house

    def detect(self) -> List[Dict]:
        growth_day = self._current_growth_day()
        if growth_day is None:
            return []

        alerts: List[Dict] = []
        alerts.extend(self._heater_drift(growth_day))
        alerts.extend(self._ventilation_drift())
        return alerts

    def _current_growth_day(self) -> Optional[int]:
        snap = self.house.monitoring_snapshots.order_by('-timestamp').first()
        if snap and snap.growth_day is not None:
            return int(snap.growth_day)
        return self.house.age_days

    def _heater_drift(self, growth_day: int) -> List[Dict]:
        caches = list(
            HouseHeaterRuntimeCache.objects.filter(
                house=self.house,
                growth_day__gte=max(0, growth_day - 7),
                growth_day__lte=growth_day,
                total_runtime_minutes__isnull=False,
            ).order_by('growth_day')
        )
        if len(caches) < 4:
            return []

        prior = [float(c.total_runtime_minutes) for c in caches[:-1]]
        current = float(caches[-1].total_runtime_minutes)
        m = mean(prior)
        sd = stdev(prior) if len(prior) > 1 else max(m * 0.1, 1.0)
        z = (current - m) / sd if sd > 0 else 0.0

        if z < self.DRIFT_Z_THRESHOLD:
            return []

        return [{
            'domain': 'equipment',
            'severity': 'high' if z >= 3.0 else 'medium',
            'message': (
                f"Heater runtime drift on growth day {growth_day}: "
                f"{current:.0f} min vs prior-week avg {m:.0f} min (z={z:.2f})."
            ),
            'payload': {
                'metric': 'heater_runtime_minutes',
                'current': current,
                'baseline_mean': m,
                'z_score': z,
                'growth_day': growth_day,
            },
        }]

    def _ventilation_drift(self) -> List[Dict]:
        since = timezone.now().date() - timedelta(days=14)
        summaries = list(
            HouseDailySummary.objects.filter(
                house=self.house,
                date__gte=since,
                ventilation_avg__isnull=False,
            ).order_by('date')
        )
        if len(summaries) < 5:
            return []

        values = [float(s.ventilation_avg) for s in summaries]
        prior = values[:-1]
        current = values[-1]
        m = mean(prior)
        sd = stdev(prior) if len(prior) > 1 else max(m * 0.1, 1.0)
        z = abs(current - m) / sd if sd > 0 else 0.0
        if z < self.DRIFT_Z_THRESHOLD:
            return []

        return [{
            'domain': 'equipment',
            'severity': 'medium',
            'message': (
                f"Ventilation level drift: latest daily avg {current:.1f}% "
                f"vs 2-week baseline {m:.1f}% (z={z:.2f})."
            ),
            'payload': {
                'metric': 'ventilation_avg',
                'current': current,
                'baseline_mean': m,
                'z_score': z,
            },
        }]
