from __future__ import annotations

from datetime import timedelta
from typing import Dict, List, Optional

from django.utils import timezone

from houses.models import HouseMonitoringSnapshot
from .anomaly_base import BaseAnomalyDetector
from .heater_runtime_metrics import (
    baseline_from_prior_windows,
    compute_heater_runtime_hours,
    filter_snapshots_in_window,
    severity_for_ratio,
    window_boundaries,
)
from .growth_day_baselines import (
    baseline_from_daily_summaries,
    daily_summaries_for_growth_day,
    get_house_growth_day,
    snapshot_baseline_same_growth_day,
    target_temperature_for_growth_day,
)
from .water_anomaly_detector import WaterAnomalyDetector


class WaterDomainDetector(BaseAnomalyDetector):
    domain = "water"

    def detect(self) -> List[Dict]:
        detector = WaterAnomalyDetector(self.house)
        anomalies = detector.detect_anomalies(days_to_check=1)
        return [
            {
                "domain": self.domain,
                "severity": item["severity"],
                "message": item["message"],
                "payload": item,
            }
            for item in anomalies
        ]


class FeedDomainDetector(BaseAnomalyDetector):
    domain = "feed"
    HIGH_RATIO = 1.35
    LOW_RATIO = 0.70

    def detect(self) -> List[Dict]:
        growth_day = get_house_growth_day(self.house)
        latest = self.house.monitoring_snapshots.order_by('-timestamp').first()
        if not latest or latest.feed_consumption is None:
            return []
        current = float(latest.feed_consumption)

        summaries = daily_summaries_for_growth_day(self.house, growth_day, limit=10)
        baseline = baseline_from_daily_summaries(summaries, 'feed_consumption_avg')
        if baseline is None:
            fallback = snapshot_baseline_same_growth_day(
                self.house, growth_day, 'feed_consumption'
            )
            if fallback is None or fallback <= 0:
                return []
            mean_val, std_val = fallback, fallback * 0.12
        else:
            mean_val, std_val = baseline

        if mean_val <= 0:
            return []
        ratio = current / mean_val
        if self.LOW_RATIO <= ratio <= self.HIGH_RATIO:
            return []

        direction = "high" if ratio > 1 else "low"
        z = abs(current - mean_val) / std_val if std_val > 0 else 0
        severity = "high" if z >= 2.5 or ratio > 1.6 or ratio < 0.55 else "medium"
        return [{
            "domain": self.domain,
            "severity": severity,
            "message": (
                f"Feed consumption anomaly ({direction}) on growth day {growth_day}: "
                f"latest {current:.2f} vs baseline {mean_val:.2f} kg/day (ratio {ratio:.2f})."
            ),
            "payload": {
                "current": current,
                "baseline": mean_val,
                "ratio": ratio,
                "direction": direction,
                "growth_day": growth_day,
            },
        }]


class TemperatureDomainDetector(BaseAnomalyDetector):
    domain = "temperature"
    HUMIDITY_HIGH = 75.0
    HUMIDITY_LOW = 45.0

    def detect(self) -> List[Dict]:
        growth_day = get_house_growth_day(self.house)
        latest = self.house.monitoring_snapshots.order_by('-timestamp').first()
        if not latest or latest.average_temperature is None:
            return []

        current_temp = float(latest.average_temperature)
        target = target_temperature_for_growth_day(self.house, growth_day)
        if target is None and latest.target_temperature is not None:
            target = float(latest.target_temperature)

        alerts: List[Dict] = []
        if target is not None:
            delta = current_temp - target
            if abs(delta) > 3.0:
                direction = "above" if delta > 0 else "below"
                severity = "high" if abs(delta) > 5.0 else "medium"
                alerts.append({
                    "domain": self.domain,
                    "severity": severity,
                    "message": (
                        f"House temperature {current_temp:.1f}°C is {abs(delta):.1f}°C {direction} "
                        f"target {target:.1f}°C (growth day {growth_day})."
                    ),
                    "parameter_name": "average_temperature",
                    "parameter_value": current_temp,
                    "threshold_value": target,
                    "payload": {"delta": delta, "growth_day": growth_day},
                })

        if latest.humidity is not None:
            hum = float(latest.humidity)
            if hum > self.HUMIDITY_HIGH:
                alerts.append({
                    "domain": "humidity",
                    "severity": "high" if hum > 85 else "medium",
                    "message": f"Humidity high: {hum:.1f}% (growth day {growth_day}).",
                    "parameter_name": "humidity",
                    "parameter_value": hum,
                    "threshold_value": self.HUMIDITY_HIGH,
                    "payload": {"growth_day": growth_day},
                })
            elif hum < self.HUMIDITY_LOW:
                alerts.append({
                    "domain": "humidity",
                    "severity": "medium",
                    "message": f"Humidity low: {hum:.1f}% (growth day {growth_day}).",
                    "parameter_name": "humidity",
                    "parameter_value": hum,
                    "threshold_value": self.HUMIDITY_LOW,
                    "payload": {"growth_day": growth_day},
                })
        return alerts


class HeaterDomainDetector(BaseAnomalyDetector):
    """
    Runtime spike vs prior 7x24h rolling windows (same heater-on semantics as KPI runtime).
    """

    domain = "heater"
    WINDOW_HOURS = 24
    MIN_SNAPSHOTS_PER_WINDOW = 4
    MIN_RUNTIME_HOURS = 2.0
    SPIKE_RATIO_THRESHOLD = 1.5
    MIN_BASELINE_SAMPLES = 3

    def detect(self) -> List[Dict]:
        now = timezone.now()
        lookback_hours = 8 * self.WINDOW_HOURS
        all_snaps = list(
            HouseMonitoringSnapshot.objects.filter(
                house=self.house,
                timestamp__gte=now - timedelta(hours=lookback_hours),
                timestamp__lte=now,
            ).order_by("timestamp")
        )
        if len(all_snaps) < self.MIN_SNAPSHOTS_PER_WINDOW:
            return []

        boundaries = window_boundaries(now, window_hours=self.WINDOW_HOURS, num_baseline_windows=7)
        runtimes: List[Optional[float]] = []
        for k, (start, end) in enumerate(boundaries):
            current_window = k == 0
            snaps = filter_snapshots_in_window(
                all_snaps, start, end, current_window=current_window
            )
            if len(snaps) < self.MIN_SNAPSHOTS_PER_WINDOW:
                runtimes.append(None)
                continue
            window_end = now if current_window else end
            rt = compute_heater_runtime_hours(snaps, window_end)
            runtimes.append(rt)

        current_rt = runtimes[0] if runtimes else None
        if current_rt is None:
            return []

        baseline = baseline_from_prior_windows(
            runtimes,
            min_baseline_samples=self.MIN_BASELINE_SAMPLES,
        )
        if baseline is None or baseline <= 0:
            return []

        if current_rt < self.MIN_RUNTIME_HOURS:
            return []

        ratio = current_rt / baseline
        if ratio < self.SPIKE_RATIO_THRESHOLD:
            return []

        severity = severity_for_ratio(ratio)
        message = (
            f"Heater runtime spike: last {self.WINDOW_HOURS}h heater runtime {current_rt:.2f} h "
            f"vs baseline {baseline:.2f} h ({ratio:.2f}x). "
            f"Investigate heating demand, stuck outputs, or sensor/controller issues."
        )
        return [
            {
                "domain": self.domain,
                "severity": severity,
                "message": message,
                "parameter_name": "heater_runtime_spike",
                "parameter_value": round(ratio, 4),
                "threshold_value": round(baseline, 4),
                "payload": {
                    "current_runtime_hours": current_rt,
                    "baseline_runtime_hours": baseline,
                    "ratio": ratio,
                    "window_hours": self.WINDOW_HOURS,
                },
            }
        ]


class VentilationDomainDetector(BaseAnomalyDetector):
    domain = "ventilation"

    def detect(self) -> List[Dict]:
        recent = list(
            HouseMonitoringSnapshot.objects.filter(
                house=self.house,
                timestamp__gte=timezone.now() - timedelta(hours=6),
            ).order_by("timestamp")
        )
        if len(recent) < 4:
            return []

        mismatches = 0
        for snap in recent:
            vent = snap.ventilation_level
            airflow = snap.airflow_percentage
            if vent is None or airflow is None:
                continue
            if abs(float(vent) - float(airflow)) > 30:
                mismatches += 1

        if mismatches >= 3:
            return [{
                "domain": self.domain,
                "severity": "medium",
                "message": "Ventilation mismatch anomaly: ventilation level and airflow are diverging.",
                "payload": {"mismatch_samples": mismatches},
            }]
        return []

