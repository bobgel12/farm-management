"""Tests for Rotem-derived flock sync and minimal flock create."""
from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from farms.models import Farm, Flock
from farms.services.rotem_flock_sync import upsert_active_flock_from_rotem
from houses.models import House, HouseMonitoringSnapshot


class RotemFlockSyncServiceTests(TestCase):
    def setUp(self):
        self.farm = Farm.objects.create(
            name="Sync Farm",
            location="Test",
            contact_person="Owner",
            contact_phone="0000000001",
            contact_email="owner@example.com",
            integration_type="rotem",
            integration_status="active",
            is_active=True,
            rotem_farm_id="rf1",
            rotem_username="u",
            rotem_password="p",
        )
        self.start = date.today() - timedelta(days=12)
        self.house = House.objects.create(
            farm=self.farm,
            house_number=2,
            capacity=8000,
            chicken_in_date=self.start,
            batch_start_date=self.start,
            current_age_days=12,
            is_active=True,
            is_integrated=True,
        )
        HouseMonitoringSnapshot.objects.create(
            house=self.house,
            bird_count=7500,
            raw_data={},
            sensor_data={},
        )

    def test_upsert_creates_active_flock(self):
        self.assertEqual(Flock.objects.filter(house=self.house).count(), 0)
        flock, created = upsert_active_flock_from_rotem(self.house)
        self.assertTrue(created)
        self.assertTrue(flock.is_active)
        self.assertEqual(flock.batch_number, "ROTEM-H2")
        self.assertEqual(flock.arrival_date, self.start)
        self.assertEqual(flock.initial_chicken_count, 7500)

    def test_upsert_updates_without_duplicating(self):
        upsert_active_flock_from_rotem(self.house)
        new_start = self.start + timedelta(days=1)
        self.house.batch_start_date = new_start
        self.house.chicken_in_date = new_start
        self.house.current_age_days = 13
        self.house.save()

        flock, created = upsert_active_flock_from_rotem(self.house)
        self.assertFalse(created)
        self.assertEqual(Flock.objects.filter(house=self.house).count(), 1)
        flock.refresh_from_db()
        self.assertEqual(flock.arrival_date, new_start)


class RotemFlockSyncApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="sync_api",
            email="sync@test.com",
            password="testpass123",
        )
        self.client.force_authenticate(user=self.user)

        self.farm_rotem = Farm.objects.create(
            name="R Farm",
            location="Test",
            contact_person="Owner",
            contact_phone="0000000003",
            contact_email="r@example.com",
            integration_type="rotem",
            integration_status="active",
            is_active=True,
            rotem_farm_id="r1",
            rotem_username="u",
            rotem_password="p",
        )
        self.start = date.today() - timedelta(days=5)
        self.house_rotem = House.objects.create(
            farm=self.farm_rotem,
            house_number=1,
            chicken_in_date=self.start,
            batch_start_date=self.start,
            current_age_days=5,
            is_active=True,
        )

        self.farm_none = Farm.objects.create(
            name="Plain Farm",
            location="Test",
            contact_person="Owner",
            contact_phone="0000000004",
            contact_email="p@example.com",
            integration_type="none",
            is_active=True,
        )
        self.house_plain = House.objects.create(
            farm=self.farm_none,
            house_number=1,
            chicken_in_date=self.start,
            current_age_days=5,
            is_active=True,
        )

    def test_sync_endpoint_rejects_non_rotem_farm(self):
        url = reverse("house-flocks-sync-from-rotem", kwargs={"house_id": self.house_plain.id})
        resp = self.client.post(url, {}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Rotem", resp.data["detail"])

    def test_sync_endpoint_creates_flock(self):
        url = reverse("house-flocks-sync-from-rotem", kwargs={"house_id": self.house_rotem.id})
        resp = self.client.post(url, {}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(resp.data["created"])
        self.assertEqual(resp.data["flock"]["batch_number"], "ROTEM-H1")


class MinimalFlockCreateApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="flock_creator",
            email="fc@test.com",
            password="testpass123",
        )
        self.client.force_authenticate(user=self.user)

        self.farm = Farm.objects.create(
            name="F Farm",
            location="Test",
            contact_person="Owner",
            contact_phone="0000000005",
            contact_email="f@example.com",
            is_active=True,
        )
        self.house = House.objects.create(
            farm=self.farm,
            house_number=4,
            capacity=6000,
            chicken_in_date=date.today(),
            is_active=True,
        )

    def test_create_with_batch_number_and_start_date_only(self):
        url = reverse("flock-list")
        start = date.today() - timedelta(days=3)
        payload = {
            "house": self.house.id,
            "batch_number": "B-100",
            "start_date": start.isoformat(),
        }
        resp = self.client.post(url, payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.data)
        self.assertEqual(resp.data["arrival_date"], start.isoformat())
        self.assertEqual(resp.data["initial_chicken_count"], 6000)
