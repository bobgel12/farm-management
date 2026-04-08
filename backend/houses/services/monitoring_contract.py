from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class MonitoringUnits:
    temperature: str = "C"
    humidity: str = "%"
    static_pressure: str = "Pa"
    water_consumption: str = "L/day"
    feed_consumption: str = "kg/day"
    airflow_cfm: str = "cfm"
    airflow_percentage: str = "%"
    ventilation_level: str = "%"


def _to_float(value: Any) -> Optional[float]:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_percent_from_ratio(value: Any) -> Optional[float]:
    number = _to_float(value)
    if number is None:
        return None
    # Normalize 0-1 ratio values into percentage.
    if 0 <= number <= 1:
        return round(number * 100.0, 2)
    return number


def normalized_snapshot_contract(snapshot) -> Dict[str, Any]:
    """
    Build a canonical monitoring payload for analytics consumers.
    The values here are unit-normalized and stable across ingestion sources.
    """
    sensor_data = snapshot.sensor_data or {}
    source_timestamp = (
        (snapshot.raw_data or {}).get("source_timestamp")
        or (snapshot.raw_data or {}).get("timestamp")
        or snapshot.timestamp.isoformat()
    )

    return {
        "source_timestamp": source_timestamp,
        "ingested_timestamp": snapshot.timestamp.isoformat(),
        "units": MonitoringUnits().__dict__,
        "environment": {
            "average_temperature": _to_float(snapshot.average_temperature),
            "outside_temperature": _to_float(snapshot.outside_temperature),
            "target_temperature": _to_float(snapshot.target_temperature),
            "humidity": _to_float(snapshot.humidity),
            "static_pressure": _to_float(snapshot.static_pressure),
        },
        "consumption": {
            "water_consumption": _to_float(snapshot.water_consumption),
            "feed_consumption": _to_float(snapshot.feed_consumption),
        },
        "ventilation": {
            "ventilation_level": _to_percent_from_ratio(snapshot.ventilation_level),
            "airflow_cfm": _to_float(snapshot.airflow_cfm),
            "airflow_percentage": _to_percent_from_ratio(snapshot.airflow_percentage),
        },
        "birds": {
            "growth_day": snapshot.growth_day,
            "bird_count": snapshot.bird_count,
            "livability": _to_float(snapshot.livability),
        },
        "connectivity": {
            "connection_status": snapshot.connection_status,
            "alarm_status": snapshot.alarm_status,
        },
        "digital_outputs": sensor_data.get("digital_outputs", {}),
    }

