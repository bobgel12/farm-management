"""Build hourly HouseFeatureSnapshot rows for ML pipelines."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Dict, List, Optional

from django.db.models import Avg, StdDev
from django.utils import timezone

from houses.models import House, HouseFeatureSnapshot, HouseMonitoringSnapshot
from rotem_scraper.models import HouseHeaterRuntimeCache

logger = logging.getLogger(__name__)


class FeatureBuilderService:
    """Materialize hourly feature vectors from monitoring snapshots."""

    @classmethod
    def build_for_house(cls, house: House, at: Optional[timezone.datetime] = None) -> Optional[HouseFeatureSnapshot]:
        at = at or timezone.now()
        hour_start = at.replace(minute=0, second=0, microsecond=0)

        window_1h = HouseMonitoringSnapshot.objects.filter(
            house=house,
            timestamp__gte=hour_start - timedelta(hours=1),
            timestamp__lte=at,
        ).order_by('timestamp')
        window_6h = HouseMonitoringSnapshot.objects.filter(
            house=house,
            timestamp__gte=hour_start - timedelta(hours=6),
            timestamp__lte=at,
        )
        window_24h = HouseMonitoringSnapshot.objects.filter(
            house=house,
            timestamp__gte=hour_start - timedelta(hours=24),
            timestamp__lte=at,
        )

        if not window_1h.exists():
            return None

        latest = window_1h.last()
        agg_1h = window_1h.aggregate(
            avg_temp=Avg('average_temperature'),
            avg_hum=Avg('humidity'),
            avg_pressure=Avg('static_pressure'),
            avg_vent=Avg('ventilation_level'),
        )
        agg_24h = window_24h.aggregate(
            water_avg=Avg('water_consumption'),
            feed_avg=Avg('feed_consumption'),
        )
        temp_std = window_6h.aggregate(std=StdDev('average_temperature'))['std']

        prev_hour_water = None
        prev_snaps = HouseMonitoringSnapshot.objects.filter(
            house=house,
            timestamp__gte=hour_start - timedelta(hours=2),
            timestamp__lt=hour_start - timedelta(hours=1),
            water_consumption__isnull=False,
        ).aggregate(w=Avg('water_consumption'))
        water_delta = None
        if agg_24h['water_avg'] is not None and prev_snaps.get('w') is not None:
            water_delta = float(agg_24h['water_avg']) - float(prev_snaps['w'])

        growth_day = latest.growth_day if latest else house.age_days
        heater_rt = None
        if growth_day is not None:
            cache = HouseHeaterRuntimeCache.objects.filter(
                house=house,
                growth_day=growth_day,
            ).order_by('-last_synced_at').first()
            if cache and cache.total_runtime_minutes is not None:
                heater_rt = float(cache.total_runtime_minutes)

        features = {
            'snapshot_count_1h': window_1h.count(),
            'snapshot_count_24h': window_24h.count(),
        }

        obj, _ = HouseFeatureSnapshot.objects.update_or_create(
            house=house,
            timestamp=hour_start,
            defaults={
                'growth_day': int(growth_day) if growth_day is not None else None,
                'bird_count': latest.bird_count if latest else None,
                'avg_temp': agg_1h['avg_temp'],
                'humidity': agg_1h['avg_hum'],
                'static_pressure': agg_1h['avg_pressure'],
                'vent_level': agg_1h['avg_vent'],
                'outside_temp': latest.outside_temperature if latest else None,
                'water_24h': agg_24h['water_avg'],
                'feed_24h': agg_24h['feed_avg'],
                'water_delta_1h': water_delta,
                'temp_std_6h': temp_std,
                'heater_runtime_24h': heater_rt,
                'features': features,
            },
        )
        return obj

    @classmethod
    def build_all_active_houses(cls) -> Dict:
        results = {'built': 0, 'skipped': 0}
        for house in House.objects.filter(is_active=True, farm__integration_type='rotem'):
            try:
                if cls.build_for_house(house):
                    results['built'] += 1
                else:
                    results['skipped'] += 1
            except Exception as exc:
                logger.exception("Feature build failed house=%s: %s", house.id, exc)
                results['skipped'] += 1
        return results
