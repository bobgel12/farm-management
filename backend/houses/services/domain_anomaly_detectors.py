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

    def detect(self) -> List[Dict]:
        recent = list(
            HouseMonitoringSnapshot.objects.filter(
                house=self.house,
                timestamp__gte=timezone.now() - timedelta(hours=24),
                feed_consumption__isnull=False,
            ).order_by("timestamp")
        )
        if len(recent) < 6:
            return []
        values = [float(s.feed_consumption) for s in recent if s.feed_consumption is not None]
        avg = sum(values) / len(values)
        current = values[-1]
        if avg <= 0:
            return []
        ratio = current / avg
        if ratio > 1.45 or ratio < 0.65:
            direction = "high" if ratio > 1 else "low"
            severity = "high" if ratio > 1.6 or ratio < 0.55 else "medium"
            return [{
                "domain": self.domain,
                "severity": severity,
                "message": f"Feed consumption anomaly ({direction}) detected: latest {current:.2f} vs 24h avg {avg:.2f} kg/day.",
                "payload": {"current": current, "baseline": avg, "ratio": ratio, "direction": direction},
            }]
        return []


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

