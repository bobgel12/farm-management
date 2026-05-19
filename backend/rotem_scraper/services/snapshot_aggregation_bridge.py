"""Bridge HouseDailySummary into RotemDailySummary on the farm controller."""
from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Dict, Optional

from django.db.models import Avg
from django.utils import timezone

from houses.models import House, HouseDailySummary
from rotem_scraper.models import RotemController, RotemDailySummary

logger = logging.getLogger(__name__)


class SnapshotAggregationBridge:
    """Sync farm-level RotemDailySummary from per-house HouseDailySummary rows."""

    @classmethod
    def sync_controller_from_houses(cls, controller: RotemController, target_date: date) -> Optional[RotemDailySummary]:
        farm = controller.farm
        if not farm:
            return None

        houses = House.objects.filter(farm=farm, is_active=True)
        summaries = HouseDailySummary.objects.filter(house__in=houses, date=target_date)
        if not summaries.exists():
            return None

        agg = summaries.aggregate(
            temp_avg=Avg('temperature_avg'),
            temp_min=Avg('temperature_min'),
            temp_max=Avg('temperature_max'),
            hum_avg=Avg('humidity_avg'),
            pressure_avg=Avg('static_pressure_avg'),
            water_avg=Avg('water_consumption_avg'),
            feed_avg=Avg('feed_consumption_avg'),
        )
        total_snaps = sum(s.snapshot_count for s in summaries)

        summary, _ = RotemDailySummary.objects.update_or_create(
            controller=controller,
            date=target_date,
            defaults={
                'temperature_avg': agg['temp_avg'],
                'temperature_min': agg['temp_min'],
                'temperature_max': agg['temp_max'],
                'humidity_avg': agg['hum_avg'],
                'static_pressure_avg': agg['pressure_avg'],
                'water_consumption_avg': agg['water_avg'],
                'feed_consumption_avg': agg['feed_avg'],
                'total_data_points': total_snaps,
            },
        )
        return summary

    @classmethod
    def sync_all_controllers(cls, target_date: Optional[date] = None) -> Dict:
        if target_date is None:
            target_date = (timezone.now() - timedelta(days=1)).date()
        results = {'date': str(target_date), 'updated': 0, 'skipped': 0}
        for controller in RotemController.objects.filter(is_connected=True).select_related('farm'):
            try:
                s = cls.sync_controller_from_houses(controller, target_date)
                if s:
                    results['updated'] += 1
                else:
                    results['skipped'] += 1
            except Exception as exc:
                logger.exception("Bridge sync failed controller=%s: %s", controller.id, exc)
                results['skipped'] += 1
        return results
