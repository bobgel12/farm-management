from datetime import date
from unittest.mock import patch

from django.test import TestCase

from farms.models import Farm
from houses.models import House, WaterConsumptionAlert
from houses.services.water_anomaly_detector import WaterAnomalyDetector
from houses.tasks import monitor_water_consumption_impl


class WaterAnomalyDetectorUnitTests(TestCase):
    def setUp(self):
        self.farm = Farm.objects.create(
            name="Farm A",
            location="Test Location",
            contact_person="Owner",
            contact_phone="0000000000",
            contact_email="owner@example.com",
            integration_type="rotem",
            integration_status="active",
            has_system_integration=True,
            is_active=True,
            rotem_farm_id="farm-a",
            rotem_username="user_a",
            rotem_password="pass_a",
        )
        self.house = House.objects.create(
            farm=self.farm,
            house_number=1,
            chicken_in_date=date.today(),
            is_active=True,
            is_integrated=True,
        )
        self.detector = WaterAnomalyDetector(self.house)

    def test_detects_high_anomaly(self):
        severity, direction, reason = self.detector._determine_anomaly(
            increase_ratio=2.1,
            baseline_std=0,
            current_consumption=210,
            expected_consumption=100,
            historical_similar_values=[95, 100, 105],
        )
        self.assertEqual(severity, "high")
        self.assertEqual(direction, "high")
        self.assertEqual(reason, "possible_leak")

    def test_detects_low_anomaly(self):
        severity, direction, reason = self.detector._determine_anomaly(
            increase_ratio=0.48,
            baseline_std=0,
            current_consumption=48,
            expected_consumption=100,
            historical_similar_values=[98, 101, 99],
        )
        self.assertEqual(severity, "high")
        self.assertEqual(direction, "low")
        self.assertEqual(reason, "possible_under_drinking")

    def test_steady_similar_age_pattern_no_alert(self):
        severity, direction, reason = self.detector._determine_anomaly(
            increase_ratio=1.08,
            baseline_std=5,
            current_consumption=108,
            expected_consumption=100,
            historical_similar_values=[104, 107, 109, 106],
        )
        self.assertIsNone(severity)
        self.assertIsNone(direction)
        self.assertEqual(reason, "normal_growth_pattern")


class WaterAnomalyTaskPersistenceTests(TestCase):
    def setUp(self):
        self.farm = Farm.objects.create(
            name="Farm B",
            location="Test Location",
            contact_person="Owner",
            contact_phone="0000000001",
            contact_email="ownerb@example.com",
            integration_type="rotem",
            integration_status="active",
            has_system_integration=True,
            is_active=True,
            rotem_farm_id="farm-b",
            rotem_username="user_b",
            rotem_password="pass_b",
        )
        self.house = House.objects.create(
            farm=self.farm,
            house_number=2,
            chicken_in_date=date.today(),
            is_active=True,
            is_integrated=True,
        )

    @patch("houses.tasks.WaterAlertEmailService.send_alert_email", return_value=False)
    @patch("houses.tasks.WaterAnomalyDetector.detect_anomalies")
    def test_task_creates_high_and_low_alerts_same_day(self, mock_detect, _mock_email):
        alert_day = date.today()
        mock_detect.return_value = [
            {
                "alert_date": alert_day,
                "growth_day": 20,
                "current_consumption": 180.0,
                "baseline_consumption": 100.0,
                "expected_consumption": 110.0,
                "increase_percentage": 80.0,
                "increase_ratio": 1.8,
                "severity": "high",
                "anomaly_direction": "high",
                "anomaly_reason": "possible_leak",
                "message": "High anomaly",
                "detection_method": "age_adjusted_statistical",
            },
            {
                "alert_date": alert_day,
                "growth_day": 20,
                "current_consumption": 50.0,
                "baseline_consumption": 100.0,
                "expected_consumption": 110.0,
                "increase_percentage": -50.0,
                "increase_ratio": 0.5,
                "severity": "high",
                "anomaly_direction": "low",
                "anomaly_reason": "possible_under_drinking",
                "message": "Low anomaly",
                "detection_method": "age_adjusted_statistical",
            },
        ]

        result = monitor_water_consumption_impl(house_id=self.house.id)
        self.assertEqual(result["alerts_created"], 2)
        self.assertEqual(
            WaterConsumptionAlert.objects.filter(house=self.house, alert_date=alert_day).count(),
            2,
        )

