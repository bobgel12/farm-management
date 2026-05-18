from datetime import date, timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from farms.models import Farm
from houses.models import FarmMonitoringCache, House, HouseMonitoringSnapshot


class HousesComparisonFastPathTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="comparison_fast_tester",
            email="comparison-fast@test.com",
            password="testpass123",
        )
        self.client.force_authenticate(user=self.user)

        self.farm = Farm.objects.create(
            name="Fast Comparison Farm",
            location="Test",
            contact_person="Owner",
            contact_phone="0000000004",
            contact_email="fast-owner@example.com",
            integration_type="rotem",
            integration_status="active",
            has_system_integration=True,
            is_active=True,
            rotem_farm_id="fast-farm",
            rotem_username="fast_user",
            rotem_password="fast_pass",
        )
        self.house = House.objects.create(
            farm=self.farm,
            house_number=1,
            chicken_in_date=date.today() - timedelta(days=12),
            is_active=True,
            is_integrated=True,
        )
        self.url = reverse("houses-comparison")

    def _cache_payload(self):
        return {
            "count": 1,
            "houses": [
                {
                    "house_id": self.house.id,
                    "house_number": self.house.house_number,
                    "farm_id": self.farm.id,
                    "farm_name": self.farm.name,
                    "water_consumption": 123,
                }
            ],
        }

    @patch("houses.views.upsert_farm_monitoring_cache")
    @patch("houses.views.RotemScraper")
    def test_cached_mode_returns_stale_cache_without_full_refresh(self, mock_scraper, mock_upsert):
        cache = FarmMonitoringCache.objects.create(
            farm=self.farm,
            comparison_payload=self._cache_payload(),
            source_timestamp=timezone.now() - timedelta(hours=1),
            refresh_state="fresh",
        )
        FarmMonitoringCache.objects.filter(id=cache.id).update(
            fetched_at=timezone.now() - timedelta(hours=1)
        )

        response = self.client.get(self.url, {"farm_id": self.farm.id, "mode": "cached"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"]["houses"][0]["water_consumption"], 123)
        mock_upsert.assert_not_called()
        mock_scraper.assert_not_called()

    @patch("houses.views.upsert_farm_monitoring_cache")
    def test_live_mode_uses_one_site_controller_call_and_updates_comparison_cache(self, mock_upsert):
        house_number = self.house.house_number

        class FakeScraper:
            calls = 0

            def __init__(self, username, password):
                pass

            def login(self):
                return True

            def get_site_controllers_info(self):
                FakeScraper.calls += 1
                return {
                    "reponseObj": {
                        "LastUpdateDT": timezone.now().isoformat(),
                        "FarmHouses": [
                            {
                                "HouseNumber": house_number,
                                "ConnectionStatus": 1,
                                "Data": {},
                            }
                        ],
                        "DicComparisonItems": {
                            "Water_Daily": {f"House{house_number}": "321"},
                            "Feed_Daily": {f"House{house_number}": "654"},
                        },
                    }
                }

        with patch("houses.views.RotemScraper", FakeScraper):
            response = self.client.get(self.url, {"farm_id": self.farm.id, "mode": "live"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(FakeScraper.calls, 1)
        self.assertEqual(response.json()["data"]["houses"][0]["water_consumption"], 321.0)
        self.assertEqual(
            FarmMonitoringCache.objects.get(farm=self.farm).comparison_payload["houses"][0]["feed_consumption"],
            654.0,
        )
        mock_upsert.assert_not_called()

    @patch("houses.views.upsert_farm_monitoring_cache")
    def test_missing_cache_falls_back_to_db_snapshot_when_live_fails(self, mock_upsert):
        HouseMonitoringSnapshot.objects.create(
            house=self.house,
            average_temperature=82.5,
            water_consumption=111,
            feed_consumption=222,
            connection_status=1,
        )

        class FailingScraper:
            def __init__(self, username, password):
                pass

            def login(self):
                return False

        with patch("houses.views.RotemScraper", FailingScraper):
            response = self.client.get(self.url, {"farm_id": self.farm.id, "mode": "cached_then_live"})

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["data"]["houses"][0]["water_consumption"], 111.0)
        self.assertEqual(payload["data"]["houses"][0]["average_temperature"], 82.5)
        self.assertEqual(payload["meta"]["source"], "db_fallback")
        self.assertIn("warning", payload["meta"])
        mock_upsert.assert_not_called()

    def test_invalid_farm_keeps_existing_404_behavior(self):
        response = self.client.get(self.url, {"farm_id": 999999, "mode": "cached"})

        self.assertEqual(response.status_code, 404)
