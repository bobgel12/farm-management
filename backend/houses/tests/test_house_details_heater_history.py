from datetime import date, timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from farms.models import Farm
from houses.models import House
from rotem_scraper.models import HouseHeaterRuntimeCache


class HouseHeaterHistoryApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="detail_tester",
            email="detail@test.com",
            password="testpass123",
        )
        self.client.force_authenticate(user=self.user)

        self.farm = Farm.objects.create(
            name="Detail Farm",
            location="Loc",
            contact_person="Owner",
            contact_phone="123456",
            contact_email="owner@example.com",
            integration_type="rotem",
            integration_status="active",
            has_system_integration=True,
            is_active=True,
            rotem_farm_id="detail-farm",
            rotem_username="user",
            rotem_password="pass",
        )
        self.house = House.objects.create(
            farm=self.farm,
            house_number=2,
            chicken_in_date=date.today() - timedelta(days=10),
            is_active=True,
            is_integrated=True,
        )

    def test_house_details_does_not_include_heater_history(self):
        response = self.client.get(
            reverse("house-details", kwargs={"house_id": self.house.id})
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("heater_history", response.json())

    def test_get_heater_history_returns_cache(self):
        HouseHeaterRuntimeCache.objects.create(
            house=self.house,
            growth_day=10,
            record_date=date.today(),
            total_runtime_minutes=180,
            per_device_json={"device_1": {"minutes": 120}, "device_2": {"minutes": 60}},
            raw_record_json={"k": "v"},
        )
        HouseHeaterRuntimeCache.objects.filter(house=self.house, growth_day=10).update(
            last_synced_at=timezone.now()
        )

        response = self.client.get(
            reverse("house-heater-history", kwargs={"house_id": self.house.id})
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["heater_history"]["summary"]["total_minutes"], 180)
        self.assertEqual(payload["heater_history"]["daily"][0]["growth_day"], 10)

    @patch("houses.views.sync_refresh_house_heater_history")
    def test_post_refresh_returns_payload(self, mock_sync):
        mock_sync.return_value = {"status": "success", "house_id": self.house.id}
        HouseHeaterRuntimeCache.objects.create(
            house=self.house,
            growth_day=1,
            record_date=date.today(),
            total_runtime_minutes=60,
            per_device_json={"device_1": {"minutes": 60}},
            raw_record_json={},
        )

        response = self.client.post(
            reverse(
                "house-heater-history-refresh", kwargs={"house_id": self.house.id}
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("heater_history", response.json())
        mock_sync.assert_called_once_with(self.house.id)
