from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from farms.models import Breed, Farm, Flock, FlockComparison, FlockPerformance
from houses.models import House
from organizations.models import Organization, OrganizationUser


class FlockApiPermissionTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="member_user",
            email="member@test.com",
            password="testpass123",
        )
        self.other_user = user_model.objects.create_user(
            username="other_user",
            email="other@test.com",
            password="testpass123",
        )
        self.staff_user = user_model.objects.create_user(
            username="staff_user",
            email="staff@test.com",
            password="testpass123",
            is_staff=True,
        )

        self.org_a = Organization.objects.create(
            name="Org A", slug="org-a", contact_email="orga@test.com"
        )
        self.org_b = Organization.objects.create(
            name="Org B", slug="org-b", contact_email="orgb@test.com"
        )
        OrganizationUser.objects.create(
            organization=self.org_a,
            user=self.user,
            role="manager",
            is_active=True,
        )

        self.farm_a = Farm.objects.create(
            organization=self.org_a,
            name="Farm A",
            location="A",
            contact_person="Owner A",
            contact_phone="0000000001",
            contact_email="fa@test.com",
            is_active=True,
        )
        self.farm_b = Farm.objects.create(
            organization=self.org_b,
            name="Farm B",
            location="B",
            contact_person="Owner B",
            contact_phone="0000000002",
            contact_email="fb@test.com",
            is_active=True,
        )
        start = date.today() - timedelta(days=10)
        self.house_a = House.objects.create(
            farm=self.farm_a,
            house_number=1,
            capacity=1000,
            chicken_in_date=start,
            current_age_days=10,
            is_active=True,
        )
        self.house_b = House.objects.create(
            farm=self.farm_b,
            house_number=2,
            capacity=1000,
            chicken_in_date=start,
            current_age_days=10,
            is_active=True,
        )
        self.breed = Breed.objects.create(name="Cobb 500", code="COBB500")
        self.flock_a = Flock.objects.create(
            house=self.house_a,
            breed=self.breed,
            batch_number="A-1",
            flock_code="A-1-code",
            arrival_date=start,
            initial_chicken_count=1000,
            current_chicken_count=980,
            created_by=self.user,
        )
        self.flock_b = Flock.objects.create(
            house=self.house_b,
            breed=self.breed,
            batch_number="B-1",
            flock_code="B-1-code",
            arrival_date=start,
            initial_chicken_count=1000,
            current_chicken_count=970,
            created_by=self.other_user,
        )
        self.performance_a = FlockPerformance.objects.create(
            flock=self.flock_a,
            record_date=date.today(),
            flock_age_days=10,
            current_chicken_count=980,
        )
        self.performance_b = FlockPerformance.objects.create(
            flock=self.flock_b,
            record_date=date.today(),
            flock_age_days=10,
            current_chicken_count=970,
        )

        self.comparison_own_org = FlockComparison.objects.create(
            name="Own Org Comparison",
            created_by=self.user,
        )
        self.comparison_own_org.flocks.set([self.flock_a])
        self.comparison_cross_org = FlockComparison.objects.create(
            name="Cross Org Comparison",
            created_by=self.user,
        )
        self.comparison_cross_org.flocks.set([self.flock_a, self.flock_b])

    def test_requires_auth_for_flock_related_endpoints(self):
        self.assertEqual(
            self.client.get(reverse("flock-list")).status_code,
            status.HTTP_401_UNAUTHORIZED,
        )
        self.assertEqual(
            self.client.get(reverse("breed-list")).status_code,
            status.HTTP_401_UNAUTHORIZED,
        )
        self.assertEqual(
            self.client.get(reverse("flock-performance-list")).status_code,
            status.HTTP_401_UNAUTHORIZED,
        )
        self.assertEqual(
            self.client.get(reverse("flock-comparison-list")).status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    @staticmethod
    def _results(payload):
        if isinstance(payload, dict) and "results" in payload:
            return payload["results"]
        return payload

    def test_non_staff_is_scoped_to_member_organizations(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.get(reverse("flock-list"))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        rows = self._results(resp.data)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["id"], self.flock_a.id)

    def test_non_staff_cannot_bypass_scope_with_query_params(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.get(
            reverse("flock-list"),
            {"organization_id": str(self.org_b.id)},
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(self._results(resp.data)), 0)

    def test_non_staff_flock_performance_is_scoped_to_member_organizations(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.get(reverse("flock-performance-list"))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        rows = self._results(resp.data)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["id"], self.performance_a.id)

    def test_non_staff_comparisons_exclude_cross_org_sets(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.get(reverse("flock-comparison-list"))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        rows = self._results(resp.data)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["id"], self.comparison_own_org.id)

    def test_staff_can_see_all_organizations(self):
        self.client.force_authenticate(user=self.staff_user)
        resp = self.client.get(reverse("flock-list"))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(self._results(resp.data)), 2)
