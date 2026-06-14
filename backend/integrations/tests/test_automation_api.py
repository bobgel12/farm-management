from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from farms.models import Farm
from integrations.models import AutomationWorkflow, IntegrationLog
from organizations.models import Organization, OrganizationUser


def _response_data(response):
    """Extract payload from standardized API envelope."""
    if isinstance(response.data, dict) and 'data' in response.data:
        return response.data['data']
    return response.data


def _response_error(response):
    if isinstance(response.data, dict) and 'error' in response.data:
        return response.data['error']
    return response.data


class AutomationWorkflowApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        user_model = get_user_model()

        self.admin_user = user_model.objects.create_user(
            username='org_admin',
            email='admin@test.com',
            password='testpass123',
        )
        self.member_user = user_model.objects.create_user(
            username='org_member',
            email='member@test.com',
            password='testpass123',
        )
        self.outsider = user_model.objects.create_user(
            username='outsider',
            email='outsider@test.com',
            password='testpass123',
        )

        self.org = Organization.objects.create(
            name='Test Org',
            slug='test-org',
            contact_email='org@test.com',
        )
        OrganizationUser.objects.create(
            organization=self.org,
            user=self.admin_user,
            role='admin',
            is_active=True,
        )
        OrganizationUser.objects.create(
            organization=self.org,
            user=self.member_user,
            role='worker',
            is_active=True,
        )

        self.farm = Farm.objects.create(
            organization=self.org,
            name='Test Farm',
            location='Here',
            contact_person='Person',
            contact_phone='0000000000',
            contact_email='farm@test.com',
            is_active=True,
        )

        self.workflow = AutomationWorkflow.objects.create(
            slug='send_report',
            name='Send Report',
            description='Send daily report via n8n',
            webhook_url='https://n8n.example.com/webhook/send-report',
            organization=self.org,
            is_active=True,
        )

        self.admin_token = Token.objects.create(user=self.admin_user)
        self.member_token = Token.objects.create(user=self.member_user)
        self.outsider_token = Token.objects.create(user=self.outsider)

    def test_list_workflows_scoped_to_user_organization(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.member_token.key}')
        response = self.client.get(
            '/api/automations/',
            {'organization_id': str(self.org.id)},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = _response_data(response)
        results = data.get('results', data) if isinstance(data, dict) else data
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['slug'], 'send_report')
        self.assertNotIn('webhook_url', results[0])

    def test_outsider_cannot_list_workflows(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.outsider_token.key}')
        response = self.client.get(
            '/api/automations/',
            {'organization_id': str(self.org.id)},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = _response_data(response)
        results = data.get('results', data) if isinstance(data, dict) else data
        self.assertEqual(len(results), 0)

    def test_admin_can_create_workflow(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.admin_token.key}')
        response = self.client.post(
            '/api/automations/',
            {
                'slug': 'sync_external',
                'name': 'Sync External',
                'webhook_url': 'https://n8n.example.com/webhook/sync',
                'organization': str(self.org.id),
                'is_active': True,
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            AutomationWorkflow.objects.filter(slug='sync_external', organization=self.org).exists()
        )

    def test_member_cannot_create_workflow(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.member_token.key}')
        response = self.client.post(
            '/api/automations/',
            {
                'slug': 'blocked',
                'name': 'Blocked',
                'webhook_url': 'https://n8n.example.com/webhook/blocked',
                'organization': str(self.org.id),
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch('integrations.n8n.requests.post')
    def test_trigger_workflow_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = 'Workflow started'
        mock_post.return_value = mock_response

        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.member_token.key}')
        response = self.client.post(
            '/api/automations/send_report/trigger/',
            {
                'organization_id': str(self.org.id),
                'farm_id': self.farm.id,
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = _response_data(response)
        self.assertEqual(data['status'], 'success')
        mock_post.assert_called_once()
        self.assertTrue(
            IntegrationLog.objects.filter(
                farm=self.farm,
                integration_type='n8n',
                action='send_report',
                status='success',
            ).exists()
        )

    @patch('integrations.n8n.requests.post')
    def test_trigger_workflow_failure_logs_error(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = 'Internal error'
        mock_post.return_value = mock_response

        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.member_token.key}')
        response = self.client.post(
            '/api/automations/send_report/trigger/',
            {'organization_id': str(self.org.id), 'farm_id': self.farm.id},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_502_BAD_GATEWAY)
        data = _response_data(response) or _response_error(response)
        self.assertEqual(data['status'], 'failed')
        self.assertTrue(
            IntegrationLog.objects.filter(
                farm=self.farm,
                integration_type='n8n',
                action='send_report',
                status='failed',
            ).exists()
        )

    def test_farm_specific_workflow_takes_priority(self):
        farm_workflow = AutomationWorkflow.objects.create(
            slug='send_report',
            name='Farm Report',
            webhook_url='https://n8n.example.com/webhook/farm-report',
            organization=self.org,
            farm=self.farm,
            is_active=True,
        )

        from integrations.n8n import resolve_workflow

        resolved = resolve_workflow(self.org.id, 'send_report', farm_id=self.farm.id)
        self.assertEqual(resolved.id, farm_workflow.id)


@override_settings(CRON_SECRET='test-cron-secret')
class N8nInboundWebhookTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_rejects_missing_cron_secret(self):
        response = self.client.post(
            '/api/webhooks/n8n/',
            {'action': 'trigger_ml_analysis'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch('integrations.webhook_views.run_ml_analysis.delay')
    def test_dispatches_ml_analysis_action(self, mock_delay):
        mock_task = MagicMock()
        mock_task.id = 'task-123'
        mock_delay.return_value = mock_task

        response = self.client.post(
            '/api/webhooks/n8n/',
            {'action': 'trigger_ml_analysis'},
            format='json',
            HTTP_X_CRON_SECRET='test-cron-secret',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = _response_data(response)
        self.assertEqual(data['task_id'], 'task-123')
        mock_delay.assert_called_once()

    def test_unknown_action_returns_400(self):
        response = self.client.post(
            '/api/webhooks/n8n/',
            {'action': 'unknown_action'},
            format='json',
            HTTP_X_CRON_SECRET='test-cron-secret',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        error = _response_error(response)
        self.assertIn('available_actions', error)
