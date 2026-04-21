from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from analytics.models import Dashboard
from organizations.models import Organization, OrganizationUser


class AutoFarmDashboardTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="farm_dashboard_user",
            email="farm-dashboard@example.com",
            password="testpass123",
        )
        self.client.force_authenticate(user=self.user)

        self.organization = Organization.objects.create(
            name="Dashboard Org",
            slug="dashboard-org",
            contact_email="org@example.com",
            created_by=self.user,
        )
        OrganizationUser.objects.create(
            organization=self.organization,
            user=self.user,
            role="owner",
            is_active=True,
        )

    def test_creating_farm_creates_one_farm_dashboard(self):
        payload = {
            "organization": str(self.organization.id),
            "name": "Auto BI Farm",
            "location": "Test Location",
            "description": "",
            "contact_person": "Owner",
            "contact_phone": "123456789",
            "contact_email": "owner@example.com",
            "is_active": True,
            "integration_type": "none",
            "integration_status": "not_configured",
            "has_system_integration": False,
        }
        response = self.client.post(reverse("farm-list"), payload, format="json")
        self.assertEqual(response.status_code, 201)
        farm_id = response.json()["id"]

        dashboards = Dashboard.objects.filter(
            organization=self.organization,
            farm_id=farm_id,
            dashboard_type="farm",
        )
        self.assertEqual(dashboards.count(), 1)
        dashboard = dashboards.first()
        self.assertIsNotNone(dashboard)
        self.assertFalse(dashboard.is_public)
        self.assertEqual(dashboard.created_by_id, self.user.id)
        self.assertEqual(dashboard.default_filters.get("farm_id"), farm_id)
