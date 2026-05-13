from datetime import date
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from farms.models import Farm
from houses.models import House
from rotem_scraper.models import HouseHeaterRuntimeCache
from rotem_scraper.scraper import RotemScraper
from rotem_scraper.tasks import sync_refresh_house_heater_history
from rotem_scraper.views import RotemDailySummaryViewSet


class Command43ParserTests(TestCase):
    def test_parse_heater_history_records(self):
        scraper = RotemScraper("u", "p")
        payload = {
            "responseObj": {
                "dsData": {
                    "Data": [
                        {
                            "HistoryRecord_Heaters_GrowthDay": -1,
                            "HistoryRecord_Heaters_HeaterDevice_1": "10:00",
                        },
                        {
                            "HistoryRecord_Heaters_GrowthDay": 8,
                            "HistoryRecord_Heaters_HeaterDevice_1": "04:23",
                            "HistoryRecord_Heaters_HeaterDevice_2": "01:00",
                        },
                    ]
                }
            }
        }
        out = scraper.parse_heater_history_records(payload)
        self.assertEqual(len(out["records"]), 1)
        self.assertIsNotNone(out["summary_row"])
        record = out["records"][0]
        self.assertEqual(record["growth_day"], 8)
        self.assertEqual(record["total_runtime_minutes"], 323)
        self.assertEqual(record["per_device"]["device_1"]["minutes"], 263)
        self.assertEqual(record["per_device"]["device_2"]["minutes"], 60)


class HeaterHistoryRefreshTaskTests(TestCase):
    def setUp(self):
        self.farm = Farm.objects.create(
            name="Task Farm",
            location="Loc",
            contact_person="Owner",
            contact_phone="000",
            contact_email="owner@example.com",
            integration_type="rotem",
            has_system_integration=True,
            rotem_username="demo",
            rotem_password="demo",
        )
        self.house = House.objects.create(
            farm=self.farm,
            house_number=1,
            chicken_in_date=date(2026, 1, 1),
            is_active=True,
            is_integrated=True,
        )

    @patch("rotem_scraper.tasks.RotemScraper")
    def test_refresh_house_heater_history_upserts(self, scraper_cls):
        scraper = scraper_cls.return_value
        scraper.login.return_value = True
        scraper.get_heater_history.return_value = {
            "source_timestamp": None,
            "summary_row": {
                "growth_day": -1,
                "is_summary_row": True,
                "total_runtime_minutes": 800,
                "total_computation_method": "sum_devices",
                "per_device": {"device_1": {"minutes": 800}},
                "raw_record": {"HistoryRecord_Heaters_GrowthDay": -1},
            },
            "records": [
                {
                    "growth_day": 1,
                    "is_summary_row": False,
                    "total_runtime_minutes": 120,
                    "total_computation_method": "sum_devices",
                    "per_device": {"device_1": {"minutes": 120}},
                    "raw_record": {"HistoryRecord_Heaters_GrowthDay": 1},
                }
            ],
        }
        result = sync_refresh_house_heater_history(self.house.id)
        self.assertEqual(result["status"], "success")
        self.assertEqual(HouseHeaterRuntimeCache.objects.filter(house=self.house).count(), 2)


class FeedHistoryApiTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = get_user_model().objects.create_user(
            username="feed-tester",
            email="feed@example.com",
            password="password",
        )
        self.farm = Farm.objects.create(
            name="Feed Farm",
            location="Loc",
            contact_person="Owner",
            contact_phone="000",
            contact_email="owner@example.com",
            integration_type="rotem",
            has_system_integration=True,
            rotem_username="demo",
            rotem_password="demo",
        )
        self.house = House.objects.create(
            farm=self.farm,
            house_number=1,
            chicken_in_date=date(2026, 1, 1),
            is_active=True,
            is_integrated=True,
        )

    @patch("rotem_scraper.views._rotem_history_command_payload")
    def test_feed_history_trims_to_requested_days(self, mock_payload):
        mock_payload.return_value = (
            [
                {
                    "HistoryRecord_GrowthDay": day,
                    "HistoryRecord_DailyFeed": str(day * 10),
                }
                for day in range(1, 7)
            ],
            None,
        )
        request = self.factory.get(
            f"/api/rotem/daily-summaries/feed-history/?house_id={self.house.id}&days=3"
        )
        force_authenticate(request, user=self.user)

        view = RotemDailySummaryViewSet.as_view({"get": "feed_history"})
        response = view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["days"], 3)
        self.assertEqual(response.data["total_days"], 3)
        self.assertEqual(
            [row["growth_day"] for row in response.data["feed_history"]],
            [4, 5, 6],
        )

    @patch("rotem_scraper.views._rotem_history_command_payload")
    def test_feed_history_all_history_returns_full_series(self, mock_payload):
        mock_payload.return_value = (
            [
                {
                    "HistoryRecord_GrowthDay": day,
                    "HistoryRecord_DailyFeed": str(day * 10),
                }
                for day in range(1, 7)
            ],
            None,
        )
        request = self.factory.get(
            f"/api/rotem/daily-summaries/feed-history/?house_id={self.house.id}&days=3&all_history=true"
        )
        force_authenticate(request, user=self.user)

        view = RotemDailySummaryViewSet.as_view({"get": "feed_history"})
        response = view(request)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["all_history"])
        self.assertEqual(response.data["total_days"], 6)
        self.assertEqual(
            [row["growth_day"] for row in response.data["feed_history"]],
            [1, 2, 3, 4, 5, 6],
        )
