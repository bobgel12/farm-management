from __future__ import annotations

from datetime import timedelta
from typing import List, Optional

from django.utils import timezone

from houses.models import House, HouseDailySummary, WaterConsumptionForecast
from rotem_scraper.models import RotemDailySummary


class WaterForecastService:
    MODEL_VERSION = "water_forecast_v2"

    def _growth_day(self, house: House) -> Optional[int]:
        snap = house.monitoring_snapshots.order_by('-timestamp').first()
        if snap and snap.growth_day is not None:
            return int(snap.growth_day)
        return house.age_days

    def _daily_water_series(self, house: House, growth_day: int) -> List[float]:
        house_rows = list(
            HouseDailySummary.objects.filter(
                house=house,
                growth_day=growth_day,
                water_consumption_avg__isnull=False,
            ).order_by('-date')[:14]
        )
        if len(house_rows) >= 3:
            return [float(r.water_consumption_avg) for r in reversed(house_rows)]

        # Fallback: any recent daily water (e.g. when growth_day shifts day-to-day)
        house_rows = list(
            HouseDailySummary.objects.filter(
                house=house,
                water_consumption_avg__isnull=False,
            ).order_by('-date')[:14]
        )
        if len(house_rows) >= 3:
            return [float(r.water_consumption_avg) for r in reversed(house_rows)]

        controller = house.farm.rotem_controllers.first()
        if not controller:
            return []
        rotem_rows = RotemDailySummary.objects.filter(
            controller=controller,
            water_consumption_avg__isnull=False,
        ).order_by('-date')[:14]
        return [float(r.water_consumption_avg) for r in reversed(rotem_rows)]

    def generate_forecasts(self, house: House, horizons: List[int] | None = None) -> List[WaterConsumptionForecast]:
        horizons = horizons or [24, 48, 72]
        growth_day = self._growth_day(house)
        if growth_day is None:
            return []

        values = self._daily_water_series(house, growth_day)
        if len(values) < 3:
            return []

        # Exponential smoothing (alpha=0.35)
        alpha = 0.35
        level = values[0]
        for v in values[1:]:
            level = alpha * v + (1 - alpha) * level
        baseline = level
        volatility = max((max(values) - min(values)) / 2.0, baseline * 0.08)

        created = []
        now = timezone.now()
        source_date = timezone.now().date()
        for horizon in horizons:
            forecast_dt = now + timedelta(hours=horizon)
            trend_factor = 1.0 + ((horizon - 24) / 24.0) * 0.015
            prediction = baseline * trend_factor
            lower = max(prediction - volatility, 0)
            upper = prediction + volatility
            confidence = max(0.45, min(0.92, 0.85 - (horizon / 200.0)))

            forecast, _ = WaterConsumptionForecast.objects.update_or_create(
                house=house,
                forecast_date=forecast_dt.replace(minute=0, second=0, microsecond=0),
                horizon_hours=horizon,
                defaults={
                    "farm": house.farm,
                    "predicted_consumption": round(prediction, 2),
                    "lower_bound": round(lower, 2),
                    "upper_bound": round(upper, 2),
                    "confidence_score": round(confidence, 3),
                    "model_version": self.MODEL_VERSION,
                    "features": {
                        "baseline_smoothed": round(baseline, 2),
                        "volatility_proxy": round(volatility, 2),
                        "growth_day": growth_day,
                        "history_days": len(values),
                    },
                    "source_date": source_date,
                },
            )
            created.append(forecast)
        return created
