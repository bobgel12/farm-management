from __future__ import annotations

from datetime import timedelta
from typing import List

from django.utils import timezone

from houses.models import House, WaterConsumptionForecast
from rotem_scraper.models import RotemDailySummary


class WaterForecastService:
    MODEL_VERSION = "water_forecast_v1"

    def generate_forecasts(self, house: House, horizons: List[int] | None = None) -> List[WaterConsumptionForecast]:
        horizons = horizons or [24, 48, 72]

        controller = house.farm.rotem_controllers.first()
        if not controller:
            return []

        recent = list(
            RotemDailySummary.objects.filter(
                controller=controller,
                water_consumption_avg__isnull=False,
            ).order_by("-date")[:7]
        )
        if len(recent) < 3:
            return []

        values = [float(item.water_consumption_avg) for item in recent]
        baseline = sum(values) / len(values)
        volatility = max((max(values) - min(values)) / 2.0, baseline * 0.08)

        created = []
        now = timezone.now()
        source_date = recent[0].date
        for horizon in horizons:
            forecast_dt = now + timedelta(hours=horizon)
            trend_factor = 1.0 + ((horizon - 24) / 24.0) * 0.02
            prediction = baseline * trend_factor
            lower = max(prediction - volatility, 0)
            upper = prediction + volatility
            confidence = max(0.45, min(0.9, 0.8 - (horizon / 240.0)))

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
                        "baseline_7d_avg": round(baseline, 2),
                        "volatility_proxy": round(volatility, 2),
                    },
                    "source_date": source_date,
                },
            )
            created.append(forecast)
        return created

