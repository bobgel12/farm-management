from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from farms.models import Farm
from houses.models import House, HouseAlarm, HouseMonitoringSnapshot


class HouseMonitoringKpisApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="kpi_tester",
            email="kpi@test.com",
            password="testpass123",
        )
        self.client.force_authenticate(user=self.user)

        self.farm = Farm.objects.create(
            name="KPI Farm",
            location="Test",
            contact_person="Owner",
            contact_phone="0000000002",
            contact_email="kpi-owner@example.com",
            integration_type="rotem",
            integration_status="active",
            has_system_integration=True,
            is_active=True,
            rotem_farm_id="kpi-farm",
            rotem_username="kpi_user",
            rotem_password="kpi_pass",
        )
        self.house = House.objects.create(
            farm=self.farm,
            house_number=3,
            chicken_in_date=date.today() - timedelta(days=15),
            is_active=True,
            is_integrated=True,
        )

    def _create_snapshot(
        self,
        timestamp,
        water,
        feed,
        heater_on=False,
        fan_on=False,
        vent_level=20,
        airflow_percentage=40,
    ):
        snapshot = HouseMonitoringSnapshot.objects.create(
            house=self.house,
            water_consumption=water,
            feed_consumption=feed,
            ventilation_level=vent_level,
            airflow_percentage=airflow_percentage,
            sensor_data={
                "digital_outputs": {
                    "heaters": {"is_on": heater_on},
                    "tunnel_fans": {"is_on": fan_on},
                }
            },
        )
        HouseMonitoringSnapshot.objects.filter(id=snapshot.id).update(timestamp=timestamp)

    def test_returns_kpis_with_runtime_and_day_over_day_deltas(self):
        now = timezone.now()
        yesterday = now - timedelta(days=1)

        # Yesterday values
        self._create_snapshot(
            timestamp=yesterday.replace(hour=8, minute=0, second=0, microsecond=0),
            water=100,
            feed=200,
            heater_on=False,
            fan_on=False,
        )
        self._create_snapshot(
            timestamp=yesterday.replace(hour=20, minute=0, second=0, microsecond=0),
            water=120,
            feed=230,
            heater_on=False,
            fan_on=True,
        )

        # Today values with heater on for 6 hours between snapshots
        self._create_snapshot(
            timestamp=now.replace(hour=6, minute=0, second=0, microsecond=0),
            water=130,
            feed=250,
            heater_on=True,
            fan_on=True,
        )
        self._create_snapshot(
            timestamp=now.replace(hour=12, minute=0, second=0, microsecond=0),
            water=150,
            feed=280,
            heater_on=False,
            fan_on=False,
        )

        HouseAlarm.objects.create(
            house=self.house,
            alarm_type="temperature",
            severity="critical",
            message="Critical temp alarm",
            is_active=True,
        )

        response = self.client.get(reverse("house-monitoring-kpis", kwargs={"house_id": self.house.id}))
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertEqual(data["house_id"], self.house.id)
        self.assertEqual(data["water_day_over_day"]["current"], 150.0)
        self.assertEqual(data["water_day_over_day"]["previous"], 120.0)
        self.assertEqual(data["water_day_over_day"]["delta"], 30.0)
        self.assertAlmostEqual(data["water_day_over_day"]["delta_pct"], 25.0, places=2)

        self.assertEqual(data["feed_day_over_day"]["current"], 280.0)
        self.assertEqual(data["feed_day_over_day"]["previous"], 230.0)
        self.assertEqual(data["feed_day_over_day"]["delta"], 50.0)

        self.assertGreaterEqual(data["heater_runtime"]["hours_24h"], 0)
        self.assertIn("method", data["heater_runtime"])
        self.assertEqual(data["alarm_burden"]["critical_24h"], 1)

    def test_returns_null_deltas_when_insufficient_data(self):
        self._create_snapshot(
            timestamp=timezone.now() - timedelta(hours=2),
            water=100,
            feed=180,
            heater_on=True,
            fan_on=False,
        )

        response = self.client.get(reverse("house-monitoring-kpis", kwargs={"house_id": self.house.id}))
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertIsNone(data["water_day_over_day"]["delta"])
        self.assertIsNone(data["feed_day_over_day"]["delta"])
        self.assertFalse(data["data_quality"]["enough_for_dod_delta"])
