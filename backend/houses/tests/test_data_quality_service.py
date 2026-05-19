from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from farms.models import Farm
from houses.models import House, HouseMonitoringSnapshot
from houses.services.data_quality_service import DataQualityService
from houses.services.house_daily_summary_service import HouseDailySummaryService


class DataQualityServiceTests(TestCase):
    def setUp(self):
        self.farm = Farm.objects.create(name='Test Farm', location='TX')
        self.house = House.objects.create(
            farm=self.farm,
            house_number=1,
            chicken_in_date=timezone.now().date(),
            chicken_out_day=40,
        )

    def test_completeness_with_snapshots(self):
        now = timezone.now()
        for i in range(5):
            HouseMonitoringSnapshot.objects.create(
                house=self.house,
                timestamp=now - timedelta(minutes=i * 5),
                average_temperature=22.0,
                connection_status=1,
            )
        metrics = DataQualityService(interval_seconds=300).house_metrics(self.house, days=1)
        self.assertEqual(metrics['snapshot_count'], 5)
        self.assertGreater(metrics['completeness_ratio'], 0)

    def test_daily_summary_aggregation(self):
        now = timezone.now()
        HouseMonitoringSnapshot.objects.create(
            house=self.house,
            timestamp=now,
            average_temperature=21.5,
            water_consumption=120.0,
            feed_consumption=80.0,
            growth_day=10,
        )
        summary = HouseDailySummaryService.aggregate_house_date(self.house, now.date(), force_update=True)
        self.assertIsNotNone(summary)
        self.assertEqual(summary.snapshot_count, 1)
        self.assertAlmostEqual(summary.water_consumption_avg, 120.0)
