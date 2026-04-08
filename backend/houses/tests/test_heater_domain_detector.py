"""Integration tests for heater runtime spike detector and orchestrator dedupe."""
from datetime import date, datetime, timedelta
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from farms.models import Farm
from houses.models import House, HouseAlarm, HouseMonitoringSnapshot
from houses.services.anomaly_orchestrator import AnomalyOrchestrator
from houses.services.domain_anomaly_detectors import HeaterDomainDetector


class CompactHeaterDetector(HeaterDomainDetector):
    """Smaller windows for faster tests."""

    WINDOW_HOURS = 1
    MIN_SNAPSHOTS_PER_WINDOW = 4
    MIN_BASELINE_SAMPLES = 3
    MIN_RUNTIME_HOURS = 0.05
    SPIKE_RATIO_THRESHOLD = 1.5


class HeaterDomainDetectorTests(TestCase):
    def setUp(self):
        self.farm = Farm.objects.create(
            name="Heater Test Farm",
            location="Test",
            contact_person="Owner",
            contact_phone="000",
            contact_email="h@test.com",
            integration_type="rotem",
            integration_status="active",
            has_system_integration=True,
            is_active=True,
            rotem_farm_id="htest",
            rotem_username="u",
            rotem_password="p",
        )
        self.house = House.objects.create(
            farm=self.farm,
            house_number=1,
            chicken_in_date=date.today() - timedelta(days=10),
            is_active=True,
            is_integrated=True,
        )

    def _snap(self, ts, heater_on: bool):
        s = HouseMonitoringSnapshot.objects.create(
            house=self.house,
            sensor_data={
                "digital_outputs": {
                    "heater_1": {"is_on": heater_on},
                }
            },
        )
        HouseMonitoringSnapshot.objects.filter(pk=s.pk).update(timestamp=ts)
        return HouseMonitoringSnapshot.objects.get(pk=s.pk)

    @patch("houses.services.domain_anomaly_detectors.timezone.now")
    def test_detects_runtime_spike_vs_baseline(self, mock_now):
        fixed = timezone.make_aware(datetime(2025, 6, 1, 12, 0, 0))
        mock_now.return_value = fixed
        wh = CompactHeaterDetector.WINDOW_HOURS

        # Baseline windows 1..7: low heater runtime (~0.25h per hour) — heater on only first 15 minutes
        for k in range(1, 8):
            w_start = fixed - timedelta(hours=(k + 1) * wh)
            for i in range(4):
                ts = w_start + timedelta(minutes=15 * i)
                self._snap(ts, heater_on=(i == 0))

        # Current window: heater on all intervals -> ~1h runtime
        w0_start = fixed - timedelta(hours=wh)
        for i in range(4):
            ts = w0_start + timedelta(minutes=15 * i)
            self._snap(ts, heater_on=True)

        det = CompactHeaterDetector(self.house)
        out = det.detect()
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["domain"], "heater")
        self.assertEqual(out[0]["parameter_name"], "heater_runtime_spike")
        self.assertIn("Heater runtime spike", out[0]["message"])
        self.assertGreater(out[0]["parameter_value"], 1.5)

    @patch("houses.services.domain_anomaly_detectors.timezone.now")
    def test_sparse_data_returns_empty(self, mock_now):
        fixed = timezone.make_aware(datetime(2025, 6, 1, 12, 0, 0))
        mock_now.return_value = fixed
        # Only one snapshot in lookback
        self._snap(fixed - timedelta(minutes=30), heater_on=True)
        det = CompactHeaterDetector(self.house)
        self.assertEqual(det.detect(), [])


class HeaterOrchestratorDedupeTests(TestCase):
    def setUp(self):
        self.farm = Farm.objects.create(
            name="Dedupe Farm",
            location="Test",
            contact_person="Owner",
            contact_phone="000",
            contact_email="d@test.com",
            integration_type="rotem",
            integration_status="active",
            has_system_integration=True,
            is_active=True,
            rotem_farm_id="dtest",
            rotem_username="u",
            rotem_password="p",
        )
        self.house = House.objects.create(
            farm=self.farm,
            house_number=2,
            chicken_in_date=date.today() - timedelta(days=5),
            is_active=True,
            is_integrated=True,
        )

    def test_second_heater_spike_not_duplicated_within_24h(self):
        orch = AnomalyOrchestrator()
        anomalies = [
            {
                "domain": "heater",
                "severity": "high",
                "message": "Heater runtime spike: test",
                "parameter_name": "heater_runtime_spike",
                "parameter_value": 2.0,
                "threshold_value": 1.0,
            }
        ]
        n1 = orch.persist_non_water_anomalies(self.house, anomalies)
        n2 = orch.persist_non_water_anomalies(self.house, anomalies)
        self.assertEqual(n1, 1)
        self.assertEqual(n2, 0)
        self.assertEqual(
            HouseAlarm.objects.filter(house=self.house, parameter_name="heater_runtime_spike").count(),
            1,
        )
