"""Unit tests for heater runtime spike helpers (no DB)."""
from datetime import datetime, timedelta

from django.test import SimpleTestCase
from django.utils import timezone

from houses.services.heater_runtime_metrics import (
    baseline_from_prior_windows,
    compute_heater_runtime_hours,
    is_heater_on,
    severity_for_ratio,
)


class _Snap:
    def __init__(self, ts, heater_on: bool):
        self.timestamp = ts
        self.sensor_data = (
            {"digital_outputs": {"heater_1": {"is_on": heater_on}}}
            if heater_on
            else {"digital_outputs": {"heater_1": {"is_on": False}}}
        )


class HeaterRuntimeMetricsTests(SimpleTestCase):
    def test_is_heater_on_detects_key(self):
        self.assertTrue(is_heater_on({"digital_outputs": {"main_heater": {"is_on": True}}}))
        self.assertFalse(is_heater_on({"digital_outputs": {"fan_1": {"is_on": True}}}))

    def test_compute_heater_runtime_two_snapshots_one_hour_on(self):
        t0 = timezone.now() - timedelta(hours=1)
        t1 = timezone.now()
        snaps = [_Snap(t0, True), _Snap(t1, True)]
        hours = compute_heater_runtime_hours(snaps, t1)
        self.assertIsNotNone(hours)
        self.assertAlmostEqual(hours, 1.0, places=2)

    def test_compute_heater_runtime_insufficient_snapshots(self):
        t0 = timezone.now()
        self.assertIsNone(compute_heater_runtime_hours([_Snap(t0, True)], t0))

    def test_baseline_mean_ignores_none(self):
        runtimes = [4.0, None, 2.0, 2.0, 2.0, None, None, None]
        b = baseline_from_prior_windows(runtimes, min_baseline_samples=3)
        self.assertAlmostEqual(b, 2.0, places=4)

    def test_severity_mapping(self):
        self.assertEqual(severity_for_ratio(1.4), "low")
        self.assertEqual(severity_for_ratio(1.5), "medium")
        self.assertEqual(severity_for_ratio(2.0), "high")
        self.assertEqual(severity_for_ratio(2.5), "critical")
