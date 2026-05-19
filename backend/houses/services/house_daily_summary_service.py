"""Aggregate HouseMonitoringSnapshot rows into HouseDailySummary."""
from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Dict, List, Optional

from django.conf import settings
from django.db.models import Avg, Max, Min
from django.utils import timezone

from houses.models import House, HouseDailySummary, HouseMonitoringSnapshot
from rotem_scraper.models import HouseHeaterRuntimeCache

logger = logging.getLogger(__name__)


class HouseDailySummaryService:
    """Build per-house daily rollups for trends and ML features."""

    @classmethod
    def expected_snapshots_per_day(cls) -> int:
        interval = getattr(settings, 'MONITORING_SNAPSHOT_INTERVAL_SECONDS', 300)
        return max(1, int(86400 / interval))

    @classmethod
    def aggregate_house_date(cls, house: House, target_date: date, force_update: bool = False) -> Optional[HouseDailySummary]:
        summary, created = HouseDailySummary.objects.get_or_create(
            house=house,
            date=target_date,
            defaults={},
        )
        if not created and not force_update:
            return summary

        start = timezone.make_aware(
            timezone.datetime.combine(target_date, timezone.datetime.min.time())
        )
        end = start + timedelta(days=1)
        snaps = HouseMonitoringSnapshot.objects.filter(
            house=house,
            timestamp__gte=start,
            timestamp__lt=end,
        )
        if not snaps.exists():
            if created:
                summary.delete()
            return None

        agg = snaps.aggregate(
            temp_avg=Avg('average_temperature'),
            temp_min=Min('average_temperature'),
            temp_max=Max('average_temperature'),
            hum_avg=Avg('humidity'),
            pressure_avg=Avg('static_pressure'),
            water_avg=Avg('water_consumption'),
            water_max=Max('water_consumption'),
            feed_avg=Avg('feed_consumption'),
            feed_max=Max('feed_consumption'),
            vent_avg=Avg('ventilation_level'),
        )
        growth_days = [
            int(g)
            for g in snaps.filter(growth_day__isnull=False).values_list('growth_day', flat=True)[:50]
            if g is not None
        ]
        growth_day = max(set(growth_days), key=growth_days.count) if growth_days else house.age_days

        heater = HouseHeaterRuntimeCache.objects.filter(
            house=house,
            record_date=target_date,
        ).first()
        if not heater and growth_day is not None:
            heater = HouseHeaterRuntimeCache.objects.filter(
                house=house,
                growth_day=growth_day,
            ).order_by('-last_synced_at').first()

        count = snaps.count()
        expected = cls.expected_snapshots_per_day()

        summary.growth_day = growth_day
        summary.temperature_avg = agg['temp_avg']
        summary.temperature_min = agg['temp_min']
        summary.temperature_max = agg['temp_max']
        summary.humidity_avg = agg['hum_avg']
        summary.static_pressure_avg = agg['pressure_avg']
        summary.water_consumption_avg = agg['water_avg']
        summary.water_consumption_max = agg['water_max']
        summary.feed_consumption_avg = agg['feed_avg']
        summary.feed_consumption_max = agg['feed_max']
        summary.ventilation_avg = agg['vent_avg']
        summary.heater_runtime_minutes = (
            float(heater.total_runtime_minutes) if heater and heater.total_runtime_minutes is not None else None
        )
        summary.snapshot_count = count
        summary.expected_snapshots = expected
        summary.completeness_ratio = min(1.0, count / expected) if expected else 0.0
        summary.save()
        return summary

    @classmethod
    def aggregate_farm(cls, farm_id: int, target_date: Optional[date] = None, force_update: bool = False) -> Dict:
        if target_date is None:
            target_date = (timezone.now() - timedelta(days=1)).date()

        houses = House.objects.filter(farm_id=farm_id, is_active=True)
        results = {'date': str(target_date), 'successful': 0, 'failed': 0, 'summaries': []}
        for house in houses:
            try:
                s = cls.aggregate_house_date(house, target_date, force_update=force_update)
                if s:
                    results['successful'] += 1
                    results['summaries'].append(s.id)
                else:
                    results['failed'] += 1
            except Exception as exc:
                logger.exception("Daily summary failed house=%s: %s", house.id, exc)
                results['failed'] += 1
        return results

    @classmethod
    def backfill_recent(cls, days: int = 7, force_update: bool = True) -> Dict:
        end_date = (timezone.now() - timedelta(days=1)).date()
        start_date = end_date - timedelta(days=days - 1)
        totals = {'days_processed': 0, 'successful': 0, 'failed': 0}
        houses = House.objects.filter(is_active=True, farm__integration_type='rotem')
        current = start_date
        while current <= end_date:
            for house in houses:
                s = cls.aggregate_house_date(house, current, force_update=force_update)
                if s:
                    totals['successful'] += 1
                else:
                    totals['failed'] += 1
            totals['days_processed'] += 1
            current += timedelta(days=1)
        return totals
