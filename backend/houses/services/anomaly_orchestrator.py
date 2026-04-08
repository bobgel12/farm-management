from __future__ import annotations

from datetime import timedelta

from typing import Dict, List

from django.utils import timezone

from houses.models import House, HouseAlarm
from .domain_anomaly_detectors import (
    FeedDomainDetector,
    HeaterDomainDetector,
    VentilationDomainDetector,
    WaterDomainDetector,
)


class AnomalyOrchestrator:
    DETECTOR_CLASSES = [
        WaterDomainDetector,
        FeedDomainDetector,
        HeaterDomainDetector,
        VentilationDomainDetector,
    ]

    def run_for_house(self, house: House) -> List[Dict]:
        anomalies: List[Dict] = []
        for detector_cls in self.DETECTOR_CLASSES:
            detector = detector_cls(house)
            anomalies.extend(detector.detect())
        return anomalies

    def persist_non_water_anomalies(self, house: House, anomalies: List[Dict]) -> int:
        created = 0
        for item in anomalies:
            domain = item.get("domain")
            if domain == "water":
                continue
            alarm_type = "equipment" if domain in {"heater", "ventilation"} else "consumption"
            param_name = item.get("parameter_name")
            # Dedupe heater runtime spikes: one active alarm per house per 24h window
            if domain == "heater" and param_name == "heater_runtime_spike":
                recent = timezone.now() - timedelta(hours=24)
                if HouseAlarm.objects.filter(
                    house=house,
                    alarm_type=alarm_type,
                    parameter_name=param_name,
                    is_active=True,
                    timestamp__gte=recent,
                ).exists():
                    continue
            HouseAlarm.objects.create(
                house=house,
                alarm_type=alarm_type,
                severity=item.get("severity", "medium"),
                message=item.get("message", ""),
                parameter_name=param_name,
                parameter_value=item.get("parameter_value"),
                threshold_value=item.get("threshold_value"),
                is_active=True,
                is_resolved=False,
            )
            created += 1
        return created

