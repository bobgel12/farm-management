"""
Heater runtime estimation from HouseMonitoringSnapshot digital_outputs (same semantics as KPI views).
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import List, Optional, Sequence, Tuple

def is_heater_on(sensor_data: Optional[dict]) -> bool:
    """True if any digital output key suggests heater is on."""
    if not sensor_data or not isinstance(sensor_data, dict):
        return False
    digital_outputs = sensor_data.get("digital_outputs") or {}
    if not isinstance(digital_outputs, dict):
        return False
    return any(
        isinstance(v, dict) and v.get("is_on") is True
        for k, v in digital_outputs.items()
        if "heater" in str(k).lower()
    )


def compute_heater_runtime_hours(
    snapshots: Sequence,
    window_end: datetime,
) -> Optional[float]:
    """
    Sum duration-weighted heater-on time for ordered snapshots within a window.
    Uses interval [snap_i, snap_{i+1}) with last interval ending at window_end.
    Returns None if insufficient data (fewer than 2 snapshots).
    """
    snaps = sorted(snapshots, key=lambda s: s.timestamp)
    if len(snaps) < 2:
        return None

    heater_seconds = 0.0
    for i, snap in enumerate(snaps):
        if i == len(snaps) - 1:
            end_time = window_end
        else:
            end_time = snaps[i + 1].timestamp
        duration = max((end_time - snap.timestamp).total_seconds(), 0.0)
        if is_heater_on(snap.sensor_data):
            heater_seconds += duration

    return round(heater_seconds / 3600.0, 4)


def window_boundaries(
    now: datetime,
    window_hours: int = 24,
    num_baseline_windows: int = 7,
) -> List[Tuple[datetime, datetime]]:
    """
    Return (start, end] boundaries for current window + prior baseline windows.
    Index 0: current [now - WH, now]
    Index k (1..7): [now - (k+1)*WH, now - k*WH)  (end exclusive for k>=1; use consistent filtering)
    """
    boundaries: List[Tuple[datetime, datetime]] = []
    wh = timedelta(hours=window_hours)
    # Current window: inclusive of both ends for snapshot filter
    boundaries.append((now - wh, now))
    for k in range(1, num_baseline_windows + 1):
        end_k = now - (k * wh)
        start_k = now - ((k + 1) * wh)
        boundaries.append((start_k, end_k))
    return boundaries


def filter_snapshots_in_window(
    snapshots: Sequence,
    start: datetime,
    end: datetime,
    *,
    current_window: bool,
) -> List:
    """Filter snapshots to time range; current window uses <= end, baseline uses < end for upper bound."""
    out = []
    for s in snapshots:
        ts = s.timestamp
        if ts < start:
            continue
        if current_window:
            if ts <= end:
                out.append(s)
        else:
            if ts < end:
                out.append(s)
    return sorted(out, key=lambda x: x.timestamp)


def baseline_from_prior_windows(
    runtimes: List[Optional[float]],
    min_baseline_samples: int = 3,
) -> Optional[float]:
    """
    runtimes[0] = current (ignored for baseline).
    runtimes[1:8] = prior 7 windows. Mean of non-None values; need at least min_baseline_samples.
    """
    vals = [r for r in runtimes[1:8] if r is not None and r >= 0]
    if len(vals) < min_baseline_samples:
        return None
    return sum(vals) / len(vals)


def severity_for_ratio(ratio: float) -> str:
    if ratio >= 2.5:
        return "critical"
    if ratio >= 2.0:
        return "high"
    if ratio >= 1.5:
        return "medium"
    return "low"
