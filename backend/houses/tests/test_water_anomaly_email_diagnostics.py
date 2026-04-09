from datetime import date, timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from farms.models import Farm
from houses.models import House, WaterConsumptionAlert
from houses.tasks import monitor_water_consumption_impl


class WaterAnomalyEmailDiagnosticsTests(TestCase):
    def setUp(self):
        self.farm = Farm.objects.create(
            name="Diag Farm",
            location="Test",
            contact_person="Owner",
            contact_phone="0000000011",
            contact_email="diag@example.com",
            integration_type="rotem",
            integration_status="active",
            has_system_integration=True,
            is_active=True,
            rotem_farm_id="diag-farm",
            rotem_username="u",
            rotem_password="p",
        )
        self.house = House.objects.create(
            farm=self.farm,
            house_number=11,
            chicken_in_date=date.today() - timedelta(days=10),
            batch_start_date=date.today() - timedelta(days=10),
            is_active=True,
            is_integrated=True,
        )

    @patch("houses.tasks.WaterForecastService.generate_forecasts", return_value=[])
    @patch("houses.tasks.AnomalyOrchestrator.run_for_house", return_value=[])
    @patch("houses.tasks.AnomalyOrchestrator.persist_non_water_anomalies", return_value=0)
    @patch("houses.tasks.WaterAlertEmailService.send_alert_email")
    @patch("houses.tasks.WaterAnomalyDetector.detect_anomalies")
    def test_anomaly_with_recipients_sends_email(
        self,
        detect_mock,
        email_mock,
        *_,
    ):
        detect_mock.return_value = [
            {
                "alert_date": date.today(),
                "growth_day": 10,
                "current_consumption": 120.0,
                "baseline_consumption": 80.0,
                "expected_consumption": 90.0,
                "increase_percentage": 50.0,
                "severity": "high",
                "anomaly_direction": "high",
                "anomaly_reason": "possible_leak",
                "message": "test",
                "detection_method": "test",
            }
        ]

        def _email_side_effect(alert, diagnostics=None, correlation_id=None):
            diagnostics.update({"recipient_count": 2})
            return True

        email_mock.side_effect = _email_side_effect
        result = monitor_water_consumption_impl(house_id=self.house.id, run_id="diag-1")
        self.assertEqual(result["alerts_created"], 1)
        self.assertEqual(result["emails_sent"], 1)
        self.assertEqual(result["correlation_id"], "diag-1")
        self.assertEqual(result["house_results"][0]["emails_sent"], 1)

    @patch("houses.tasks.WaterForecastService.generate_forecasts", return_value=[])
    @patch("houses.tasks.AnomalyOrchestrator.run_for_house", return_value=[])
    @patch("houses.tasks.AnomalyOrchestrator.persist_non_water_anomalies", return_value=0)
    @patch("houses.tasks.WaterAlertEmailService.send_alert_email")
    @patch("houses.tasks.WaterAnomalyDetector.detect_anomalies")
    def test_anomaly_with_no_recipients_sets_reason(
        self,
        detect_mock,
        email_mock,
        *_,
    ):
        detect_mock.return_value = [
            {
                "alert_date": date.today(),
                "growth_day": 10,
                "current_consumption": 120.0,
                "baseline_consumption": 80.0,
                "expected_consumption": 90.0,
                "increase_percentage": 50.0,
                "severity": "high",
                "anomaly_direction": "high",
                "anomaly_reason": "possible_leak",
                "message": "test",
                "detection_method": "test",
            }
        ]

        def _email_side_effect(alert, diagnostics=None, correlation_id=None):
            diagnostics.update({"recipient_count": 0, "suppression_reason": "no_recipients"})
            return False

        email_mock.side_effect = _email_side_effect
        result = monitor_water_consumption_impl(house_id=self.house.id, run_id="diag-2")
        self.assertEqual(result["alerts_created"], 1)
        self.assertEqual(result["emails_sent"], 0)
        self.assertEqual(result["house_results"][0]["suppression_reason"], "no_recipients")

    @patch("houses.tasks.WaterForecastService.generate_forecasts", return_value=[])
    @patch("houses.tasks.AnomalyOrchestrator.run_for_house", return_value=[])
    @patch("houses.tasks.AnomalyOrchestrator.persist_non_water_anomalies", return_value=0)
    @patch("houses.tasks.WaterAlertEmailService.send_alert_email")
    @patch("houses.tasks.WaterAnomalyDetector.detect_anomalies")
    def test_duplicate_alert_same_day_skips_email(
        self,
        detect_mock,
        email_mock,
        *_,
    ):
        alert_date = date.today()
        detect_mock.return_value = [
            {
                "alert_date": alert_date,
                "growth_day": 10,
                "current_consumption": 120.0,
                "baseline_consumption": 80.0,
                "expected_consumption": 90.0,
                "increase_percentage": 50.0,
                "severity": "high",
                "anomaly_direction": "high",
                "anomaly_reason": "possible_leak",
                "message": "test",
                "detection_method": "test",
            }
        ]
        WaterConsumptionAlert.objects.create(
            house=self.house,
            farm=self.farm,
            alert_date=alert_date,
            growth_day=10,
            current_consumption=120.0,
            baseline_consumption=80.0,
            increase_percentage=50.0,
            severity="high",
            anomaly_direction="high",
            anomaly_reason="possible_leak",
            message="existing",
            detection_method="test",
        )
        result = monitor_water_consumption_impl(house_id=self.house.id, run_id="diag-3")
        self.assertEqual(result["alerts_created"], 0)
        self.assertEqual(result["emails_sent"], 0)
        self.assertEqual(result["house_results"][0]["suppression_reason"], "duplicate_alert_same_day")
        email_mock.assert_not_called()

    @patch("houses.tasks.WaterForecastService.generate_forecasts", return_value=[])
    @patch("houses.tasks.AnomalyOrchestrator.run_for_house", return_value=[])
    @patch("houses.tasks.AnomalyOrchestrator.persist_non_water_anomalies", return_value=0)
    @patch("houses.tasks.WaterAnomalyDetector.detect_anomalies")
    def test_no_anomaly_reason_propagates(self, detect_mock, *_):
        def _detect(days_to_check=1, diagnostics=None, correlation_id=None):
            diagnostics.append({"reason": "normal_growth_pattern"})
            return []

        detect_mock.side_effect = _detect
        result = monitor_water_consumption_impl(house_id=self.house.id, run_id="diag-4")
        self.assertEqual(result["alerts_created"], 0)
        self.assertEqual(result["emails_sent"], 0)
        self.assertEqual(result["house_results"][0]["suppression_reason"], "normal_growth_pattern")


class TriggerWaterAnomalyResponseTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        user_model = get_user_model()
        user = user_model.objects.create_user(
            username="water_diag",
            email="water_diag@test.com",
            password="testpass123",
        )
        self.client.force_authenticate(user=user)
        self.farm = Farm.objects.create(
            name="Diag Farm 2",
            location="Test",
            contact_person="Owner",
            contact_phone="0000000012",
            contact_email="diag2@example.com",
            integration_type="rotem",
            integration_status="active",
            has_system_integration=True,
            is_active=True,
            rotem_farm_id="diag-farm-2",
            rotem_username="u",
            rotem_password="p",
        )
        self.house = House.objects.create(
            farm=self.farm,
            house_number=12,
            chicken_in_date=date.today() - timedelta(days=10),
            is_active=True,
            is_integrated=True,
        )

    @patch("houses.tasks.monitor_water_consumption_impl")
    def test_sync_trigger_returns_house_results_summary(self, impl_mock):
        impl_mock.return_value = {
            "status": "success",
            "houses_checked": 1,
            "alerts_created": 0,
            "emails_sent": 0,
            "correlation_id": "manual-123",
            "house_results": [
                {
                    "house_id": self.house.id,
                    "suppression_reason": "no_recipients",
                }
            ],
        }
        url = reverse("trigger-water-anomaly-detection", kwargs={"house_id": self.house.id})
        resp = self.client.post(url, {"run_sync": True, "correlation_id": "manual-123"}, format="json")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["correlation_id"], "manual-123")
        self.assertIn("house_results", resp.data)
