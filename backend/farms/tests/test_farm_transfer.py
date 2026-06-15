from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from analytics.models import Dashboard
from farms.models import Farm
from houses.models import House
from integrations.models import AutomationWorkflow
from organizations.models import Organization, OrganizationUser


def _response_data(response):
    if isinstance(response.data, dict) and 'data' in response.data:
        return response.data['data'] or response.data.get('error')
    return response.data


class FarmTransferApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        user_model = get_user_model()

        self.admin_user = user_model.objects.create_user(
            username='transfer_admin',
            email='admin@test.com',
            password='testpass123',
        )
        self.member_user = user_model.objects.create_user(
            username='transfer_member',
            email='member@test.com',
            password='testpass123',
        )

        self.org_source = Organization.objects.create(
            name='Source Org',
            slug='source-org',
            contact_email='source@test.com',
            max_farms=5,
        )
        self.org_target = Organization.objects.create(
            name='Target Org',
            slug='target-org',
            contact_email='target@test.com',
            max_farms=5,
        )
        self.org_full = Organization.objects.create(
            name='Full Org',
            slug='full-org',
            contact_email='full@test.com',
            max_farms=0,
        )

        OrganizationUser.objects.create(
            organization=self.org_source,
            user=self.admin_user,
            role='owner',
            is_active=True,
        )
        OrganizationUser.objects.create(
            organization=self.org_target,
            user=self.admin_user,
            role='admin',
            is_active=True,
        )
        OrganizationUser.objects.create(
            organization=self.org_full,
            user=self.admin_user,
            role='owner',
            is_active=True,
        )
        OrganizationUser.objects.create(
            organization=self.org_source,
            user=self.member_user,
            role='worker',
            is_active=True,
        )

        self.farm = Farm.objects.create(
            organization=self.org_source,
            name='Transfer Farm',
            location='Here',
            contact_person='Person',
            contact_phone='0000000000',
            contact_email='farm@test.com',
            is_active=True,
        )
        House.objects.create(
            farm=self.farm,
            house_number=1,
            capacity=1000,
            chicken_in_date=date.today() - timedelta(days=5),
            current_age_days=5,
            is_active=True,
        )

        self.dashboard = Dashboard.objects.create(
            name='Farm BI',
            dashboard_type='farm',
            organization=self.org_source,
            farm=self.farm,
            created_by=self.admin_user,
        )
        self.workflow = AutomationWorkflow.objects.create(
            slug='farm_report',
            name='Farm Report',
            webhook_url='https://n8n.example.com/webhook/farm-report',
            organization=self.org_source,
            farm=self.farm,
            is_active=True,
        )

        self.admin_token = Token.objects.create(user=self.admin_user)
        self.member_token = Token.objects.create(user=self.member_user)

    def test_transfer_success(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.admin_token.key}')
        response = self.client.post(
            f'/api/farms/{self.farm.id}/transfer/',
            {'target_organization_id': str(self.org_target.id)},
            format='json',
        )
        data = _response_data(response)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(data['status'], 'success')

        self.farm.refresh_from_db()
        self.assertEqual(self.farm.organization_id, self.org_target.id)

        self.dashboard.refresh_from_db()
        self.assertEqual(self.dashboard.organization_id, self.org_target.id)

        self.workflow.refresh_from_db()
        self.assertEqual(self.workflow.organization_id, self.org_target.id)

    def test_member_cannot_transfer(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.member_token.key}')
        response = self.client.post(
            f'/api/farms/{self.farm.id}/transfer/',
            {'target_organization_id': str(self.org_target.id)},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cannot_transfer_to_same_org(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.admin_token.key}')
        response = self.client.post(
            f'/api/farms/{self.farm.id}/transfer/',
            {'target_organization_id': str(self.org_source.id)},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_transfer_when_target_at_limit(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.admin_token.key}')
        response = self.client.post(
            f'/api/farms/{self.farm.id}/transfer/',
            {'target_organization_id': str(self.org_full.id)},
            format='json',
        )
        data = _response_data(response)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(data.get('code'), 'farm_limit_reached')

    def test_farm_list_scoped_after_transfer(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.admin_token.key}')
        self.client.post(
            f'/api/farms/{self.farm.id}/transfer/',
            {'target_organization_id': str(self.org_target.id)},
            format='json',
        )

        source_response = self.client.get(
            '/api/farms/',
            {'organization_id': str(self.org_source.id)},
        )
        source_data = _response_data(source_response)
        source_results = source_data.get('results', source_data) if isinstance(source_data, dict) else source_data
        source_ids = [f['id'] for f in source_results]

        target_response = self.client.get(
            '/api/farms/',
            {'organization_id': str(self.org_target.id)},
        )
        target_data = _response_data(target_response)
        target_results = target_data.get('results', target_data) if isinstance(target_data, dict) else target_data
        target_ids = [f['id'] for f in target_results]
        self.assertNotIn(self.farm.id, source_ids)
        self.assertIn(self.farm.id, target_ids)

    def test_organization_not_writable_via_patch(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.admin_token.key}')
        response = self.client.patch(
            f'/api/farms/{self.farm.id}/',
            {'organization': str(self.org_target.id)},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.farm.refresh_from_db()
        self.assertEqual(self.farm.organization_id, self.org_source.id)
