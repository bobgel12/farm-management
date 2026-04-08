from __future__ import annotations

from datetime import timedelta
from typing import Dict, List

from django.utils import timezone

from houses.models import HouseMonitoringSnapshot
from .anomaly_base import BaseAnomalyDetector
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
    domain = "heater"

    def detect(self) -> List[Dict]:
        recent = list(
            HouseMonitoringSnapshot.objects.filter(
                house=self.house,
                timestamp__gte=timezone.now() - timedelta(hours=6),
            ).order_by("timestamp")
        )
        if len(recent) < 4:
            return []

        heater_on_count = 0
        missing_target_while_heater = 0
        for snap in recent:
            outputs = (snap.sensor_data or {}).get("digital_outputs", {})
            heater_on = any(
                isinstance(v, dict) and v.get("is_on") is True
                for k, v in outputs.items()
                if "heater" in k
            )
            if heater_on:
                heater_on_count += 1
                if snap.average_temperature is not None and snap.target_temperature is not None:
                    if float(snap.average_temperature) + 1.5 < float(snap.target_temperature):
                        missing_target_while_heater += 1

        if heater_on_count >= 3 and missing_target_while_heater >= 3:
            return [{
                "domain": self.domain,
                "severity": "high",
                "message": "Heater inefficiency anomaly: heater active but temperature remains below target.",
                "payload": {
                    "heater_on_samples": heater_on_count,
                    "target_miss_samples": missing_target_while_heater,
                },
            }]
        return []


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

