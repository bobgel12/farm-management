from datetime import date, timedelta
from unittest.mock import patch
import uuid

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from farms.models import Farm
from houses.models import FarmMonitoringCache, House, MonitoringCacheRefreshRun
from houses.services.monitoring_cache_run_service import (
    claim_next_queued_manual_run,
    execute_refresh_run,
    queue_manual_refresh_run,
)

class MonitoringCacheRefreshTestBase(TestCase):
    def setUp(self):
        self.client = APIClient()
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="monitoring_cache_tester",
            email="monitoring-cache@test.com",
            password="testpass123",
            is_staff=True,
        )
        self.client.force_authenticate(user=self.user)

        self.farm = Farm.objects.create(
            name="Cache Test Farm",
            location="Test",
            contact_person="Owner",
            contact_phone="0000000099",
            contact_email="cache-owner@example.com",
            integration_type="rotem",
            integration_status="active",
            has_system_integration=True,
            is_active=True,
            rotem_farm_id="cache-farm",
            rotem_username="cache_user",
            rotem_password="cache_pass",
        )
        self.house = House.objects.create(
            farm=self.farm,
            house_number=1,
            chicken_in_date=date.today() - timedelta(days=10),
            is_active=True,
            is_integrated=True,
        )
        self.dashboard_payload = {
            "farm_id": self.farm.id,
            "farm_name": self.farm.name,
            "total_houses": 1,
            "houses": [{"house_id": self.house.id, "house_number": 1}],
            "alerts_summary": {"total_active": 0, "critical": 0, "warning": 0, "normal": 1},
            "connection_summary": {"connected": 1, "disconnected": 0},
        }


class CacheOnlyModeTests(MonitoringCacheRefreshTestBase):
    def test_cache_only_dashboard_returns_cache_without_rotem(self):
        cache = FarmMonitoringCache.objects.create(
            farm=self.farm,
            dashboard_payload=self.dashboard_payload,
            source_timestamp=timezone.now(),
            refresh_state="fresh",
        )
        FarmMonitoringCache.objects.filter(id=cache.id).update(
            fetched_at=timezone.now() - timedelta(minutes=2)
        )

        url = reverse("farm-houses-monitoring-dashboard", kwargs={"farm_id": self.farm.id})
        with patch("houses.views._ensure_farm_cache") as mock_ensure, patch(
            "houses.views.RotemScraper"
        ) as mock_scraper:
            response = self.client.get(url, {"mode": "cache_only"})

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["data"]["total_houses"], 1)
        self.assertIn("meta", body)
        mock_ensure.assert_not_called()
        mock_scraper.assert_not_called()

    def test_cache_only_missing_cache_returns_empty_payload_with_metadata(self):
        url = reverse("farm-houses-monitoring-dashboard", kwargs={"farm_id": self.farm.id})
        with patch("houses.views._ensure_farm_cache") as mock_ensure, patch(
            "houses.views.RotemScraper"
        ) as mock_scraper:
            response = self.client.get(url, {"mode": "cache_only"})

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["data"]["total_houses"], 0)
        self.assertEqual(body["meta"]["refresh_state"], "missing")
        mock_ensure.assert_not_called()
        mock_scraper.assert_not_called()


class MonitoringCacheRefreshApiTests(MonitoringCacheRefreshTestBase):
    def test_manual_refresh_queue_returns_run_id(self):
        url = reverse("monitoring-cache-refresh-queue")
        response = self.client.post(url, {}, format="json")

        self.assertIn(response.status_code, (status.HTTP_200_OK, status.HTTP_202_ACCEPTED))
        body = response.json()
        self.assertIn("run_id", body)
        self.assertEqual(body["trigger_type"], "manual")
        self.assertEqual(body["status"], "queued")
        run = MonitoringCacheRefreshRun.objects.get(run_id=body["run_id"])
        self.assertEqual(run.requested_by_id, self.user.id)

    def test_manual_refresh_dedupes_active_run(self):
        url = reverse("monitoring-cache-refresh-queue")
        first = self.client.post(url, {}, format="json").json()
        second = self.client.post(url, {}, format="json").json()
        self.assertEqual(first["run_id"], second["run_id"])
        self.assertEqual(
            MonitoringCacheRefreshRun.objects.filter(trigger_type="manual").count(),
            1,
        )

    def test_refresh_run_detail_returns_status(self):
        run = MonitoringCacheRefreshRun.objects.create(
            run_id=uuid.uuid4(),
            trigger_type="manual",
            status="success",
            farms_processed=1,
            houses_processed=2,
            completed_at=timezone.now(),
        )
        url = reverse("monitoring-cache-refresh-run-detail", kwargs={"run_id": run.run_id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["run_id"], str(run.run_id))
        self.assertEqual(body["status"], "success")
        self.assertEqual(body["houses_processed"], 2)


class FarmCacheStatusTests(MonitoringCacheRefreshTestBase):
    def test_cache_status_reports_freshness_and_latest_runs(self):
        fetched_at = timezone.now() - timedelta(minutes=12)
        cache = FarmMonitoringCache.objects.create(
            farm=self.farm,
            dashboard_payload=self.dashboard_payload,
            source_timestamp=fetched_at,
            refresh_state="stale",
        )
        FarmMonitoringCache.objects.filter(id=cache.id).update(fetched_at=fetched_at)

        scheduled = MonitoringCacheRefreshRun.objects.create(
            run_id=uuid.uuid4(),
            trigger_type="scheduled",
            status="success",
            completed_at=timezone.now(),
        )
        manual = MonitoringCacheRefreshRun.objects.create(
            run_id=uuid.uuid4(),
            trigger_type="manual",
            status="partial",
            completed_at=timezone.now(),
        )

        url = reverse("farm-monitoring-cache-status", kwargs={"farm_id": self.farm.id})
        with patch.dict("os.environ", {"MONITORING_CACHE_INTERVAL_SECONDS": "600"}):
            response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["farm_id"], self.farm.id)
        self.assertTrue(body["cache"]["exists"])
        self.assertIsNotNone(body["cache"]["fetched_at"])
        self.assertGreater(body["cache"]["age_seconds"], 0)
        self.assertTrue(body["cache"]["is_stale"])
        self.assertEqual(body["worker_interval_seconds"], 600)
        self.assertEqual(body["latest_runs"]["scheduled"]["run_id"], str(scheduled.run_id))
        self.assertEqual(body["latest_runs"]["manual"]["status"], "partial")


class MonitoringCacheRunServiceTests(MonitoringCacheRefreshTestBase):
    def test_claim_next_queued_manual_run_marks_running(self):
        run = MonitoringCacheRefreshRun.objects.create(
            run_id=uuid.uuid4(),
            trigger_type="manual",
            status="queued",
        )
        claimed = claim_next_queued_manual_run()
        self.assertIsNotNone(claimed)
        self.assertEqual(str(claimed.run_id), str(run.run_id))
        run.refresh_from_db()
        self.assertEqual(run.status, "running")
        self.assertIsNotNone(run.started_at)

    @patch("houses.services.monitoring_cache_run_service._refresh_one_farm")
    def test_execute_refresh_run_records_partial_when_some_farms_fail(self, mock_refresh):
        other_farm = Farm.objects.create(
            name="Other Cache Farm",
            location="Test",
            contact_person="Owner",
            contact_phone="0000000100",
            contact_email="other-cache@example.com",
            integration_type="rotem",
            integration_status="active",
            has_system_integration=True,
            is_active=True,
            rotem_farm_id="other-cache-farm",
        )

        def side_effect(farm_id: int):
            if farm_id == self.farm.id:
                return {
                    "farm_id": self.farm.id,
                    "farm_name": self.farm.name,
                    "status": "success",
                    "message": "ok",
                    "houses_processed": 1,
                }
            return {
                "farm_id": farm_id,
                "status": "failed",
                "message": "login_failed",
                "houses_processed": 0,
            }

        mock_refresh.side_effect = side_effect

        run = MonitoringCacheRefreshRun.objects.create(
            run_id=uuid.uuid4(),
            trigger_type="manual",
            status="running",
            started_at=timezone.now(),
        )
        finished = execute_refresh_run(run)
        self.assertEqual(finished.status, "partial")
        self.assertEqual(finished.farms_processed, 1)
        self.assertEqual(finished.houses_processed, 1)
        self.assertIn("login_failed", finished.error_summary)
        farm_rows = {row["farm_id"]: row for row in finished.result_payload["farms"]}
        self.assertEqual(farm_rows[self.farm.id]["status"], "success")
        self.assertEqual(farm_rows[other_farm.id]["status"], "failed")

    @patch("houses.services.monitoring_cache_run_service.upsert_farm_monitoring_cache")
    def test_queue_manual_refresh_run_creates_queued_run(self, mock_upsert):
        run = queue_manual_refresh_run(self.user)
        self.assertEqual(run.status, "queued")
        self.assertEqual(run.trigger_type, "manual")
        mock_upsert.assert_not_called()
