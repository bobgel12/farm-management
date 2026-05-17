from datetime import date, timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from farms.models import Farm
from houses.models import House, HouseMonitoringCache


def raw_history(*rows):
    return {
        "reponseObj": {
            "dsData": {
                "Data": [
                    {
                        "HistoryRecord_GrowthDay": growth_day,
                        "HistoryRecord_TotalDrink": water,
                        "HistoryRecord_FeederTotal": feed,
                    }
                    for growth_day, water, feed in rows
                ]
            }
        }
    }


class FarmWaterHistoryComparisonApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="water_compare_tester",
            email="water-compare@test.com",
            password="testpass123",
        )
        self.client.force_authenticate(user=self.user)

        self.farm = Farm.objects.create(
            name="Water Compare Farm",
            location="Test",
            contact_person="Owner",
            contact_phone="0000000003",
            contact_email="water-owner@example.com",
            integration_type="rotem",
            integration_status="active",
            has_system_integration=True,
            is_active=True,
            rotem_farm_id="water-farm",
            rotem_username="water_user",
            rotem_password="water_pass",
        )
        self.house_a = House.objects.create(
            farm=self.farm,
            house_number=1,
            chicken_in_date=date(2026, 5, 1),
            batch_start_date=date(2026, 5, 1),
            is_active=True,
            is_integrated=True,
        )
        self.house_b = House.objects.create(
            farm=self.farm,
            house_number=2,
            chicken_in_date=date(2026, 5, 1),
            batch_start_date=date(2026, 5, 1),
            is_active=True,
            is_integrated=True,
        )

    def _url(self):
        return reverse("farm-water-history-comparison", kwargs={"farm_id": self.farm.id})

    def _cache(self, house, fetched_at, rows):
        cache = HouseMonitoringCache.objects.create(
            house=house,
            water_history_payload=rows,
            water_history_fetched_at=fetched_at,
        )
        return cache

    @patch("houses.views.RotemScraper")
    def test_fresh_cache_returns_without_rotem(self, mock_scraper):
        self._cache(
            self.house_a,
            timezone.now(),
            [
                {"date": "2026-05-16", "consumption_avg": 100, "feed_consumption": 200},
                {"date": "2026-05-17", "consumption_avg": 125, "feed_consumption": 240},
            ],
        )

        response = self.client.get(self._url(), {"dod_reference_date": "2026-05-17"})

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        row = payload["houses"][str(self.house_a.id)]
        self.assertEqual(row["source"], "cache")
        self.assertEqual(row["water_day_over_day"]["current"], 125.0)
        self.assertEqual(row["water_day_over_day"]["previous"], 100.0)
        self.assertEqual(row["water_day_over_day"]["delta"], 25.0)
        self.assertEqual(row["feed_day_over_day"]["delta"], 40.0)
        mock_scraper.assert_not_called()

    def test_stale_cache_fetches_only_stale_houses_and_updates_cache(self):
        self._cache(
            self.house_a,
            timezone.now(),
            [
                {"date": "2026-05-16", "consumption_avg": 10, "feed_consumption": 20},
                {"date": "2026-05-17", "consumption_avg": 15, "feed_consumption": 25},
            ],
        )
        self._cache(
            self.house_b,
            timezone.now() - timedelta(hours=1),
            [{"date": "2026-05-16", "consumption_avg": 1, "feed_consumption": 2}],
        )
        calls = []

        class FakeScraper:
            def __init__(self, username, password):
                pass

            def login(self):
                return True

            def get_water_history(self, house_number):
                calls.append(house_number)
                return raw_history((15, 300, 400), (16, 330, 430))

        with patch("houses.views.RotemScraper", FakeScraper):
            response = self.client.get(self._url(), {"dod_reference_date": "2026-05-17"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(calls, [self.house_b.house_number])
        payload = response.json()
        self.assertEqual(payload["houses"][str(self.house_a.id)]["source"], "cache")
        self.assertEqual(payload["houses"][str(self.house_b.id)]["source"], "live")
        self.assertEqual(payload["houses"][str(self.house_b.id)]["water_day_over_day"]["delta"], 30.0)
        self.assertEqual(
            HouseMonitoringCache.objects.get(house=self.house_b).water_history_payload[-1]["feed_consumption"],
            430.0,
        )

    def test_house_failure_returns_partial_payload(self):
        failing_house_number = self.house_b.house_number

        class FailingScraper:
            def __init__(self, username, password):
                pass

            def login(self):
                return True

            def get_water_history(self, house_number):
                if house_number == failing_house_number:
                    raise RuntimeError("Rotem timeout")
                return raw_history((15, 100, 200), (16, 120, 210))

        with patch("houses.views.RotemScraper", FailingScraper):
            response = self.client.get(self._url(), {"dod_reference_date": "2026-05-17"})

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["meta"]["partial"])
        self.assertEqual(payload["houses"][str(self.house_a.id)]["source"], "live")
        self.assertEqual(payload["houses"][str(self.house_b.id)]["source"], "failed")
        self.assertIn("Rotem timeout", payload["houses"][str(self.house_b.id)]["error"])

    def test_invalid_reference_date_returns_400(self):
        response = self.client.get(self._url(), {"dod_reference_date": "not-a-date"})

        self.assertEqual(response.status_code, 400)
        self.assertIn("detail", response.json())

    def test_unauthenticated_request_is_rejected(self):
        self.client.force_authenticate(user=None)

        response = self.client.get(self._url())

        self.assertIn(response.status_code, [401, 403])
