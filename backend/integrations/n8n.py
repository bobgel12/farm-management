import logging
import time
from typing import Any, Dict, Optional, Tuple

import requests
from django.contrib.auth.models import User
from django.utils import timezone

from farms.models import Farm

from .models import AutomationWorkflow, IntegrationLog

logger = logging.getLogger(__name__)


def resolve_workflow(
    organization_id,
    slug: str,
    farm_id: Optional[int] = None,
) -> Optional[AutomationWorkflow]:
    """Prefer farm-specific workflow, then org-wide (farm=null)."""
    base_qs = AutomationWorkflow.objects.filter(
        organization_id=organization_id,
        slug=slug,
        is_active=True,
    )
    if farm_id:
        farm_specific = base_qs.filter(farm_id=farm_id).first()
        if farm_specific:
            return farm_specific
    return base_qs.filter(farm__isnull=True).first()


def resolve_log_farm(
    organization_id,
    farm_id: Optional[int] = None,
    workflow_farm: Optional[Farm] = None,
) -> Optional[Farm]:
    if farm_id:
        return Farm.objects.filter(id=farm_id, organization_id=organization_id).first()
    if workflow_farm:
        return workflow_farm
    return Farm.objects.filter(organization_id=organization_id).order_by('id').first()


class N8nTriggerService:
    """Trigger n8n webhook workflows and log results."""

    def build_payload(
        self,
        workflow: AutomationWorkflow,
        user: User,
        farm: Optional[Farm] = None,
        extra_payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        return {
            'workflow_slug': workflow.slug,
            'triggered_by_user_id': user.id,
            'triggered_by_email': user.email,
            'organization_id': str(workflow.organization_id),
            'farm_id': farm.id if farm else None,
            'farm_name': farm.name if farm else None,
            'timestamp': timezone.now().isoformat(),
            'payload': extra_payload or {},
        }

    def trigger(
        self,
        workflow: AutomationWorkflow,
        user: User,
        farm: Optional[Farm] = None,
        extra_payload: Optional[Dict[str, Any]] = None,
        test_mode: bool = False,
    ) -> Dict[str, Any]:
        payload = self.build_payload(workflow, user, farm, extra_payload)
        if test_mode:
            payload['test'] = True

        headers = {'Content-Type': 'application/json'}
        if workflow.webhook_secret:
            headers['X-Webhook-Secret'] = workflow.webhook_secret

        start = time.time()
        try:
            response = requests.post(
                workflow.webhook_url,
                json=payload,
                headers=headers,
                timeout=30,
            )
            execution_time = time.time() - start
            success = 200 <= response.status_code < 300
            message = response.text[:500] if response.text else f'HTTP {response.status_code}'
            status_label = 'success' if success else 'failed'

            log_farm = farm or resolve_log_farm(
                workflow.organization_id,
                farm_id=farm.id if farm else None,
                workflow_farm=workflow.farm,
            )
            if log_farm:
                IntegrationLog.objects.create(
                    farm=log_farm,
                    integration_type='n8n',
                    action=f"{'test_' if test_mode else ''}{workflow.slug}",
                    status=status_label,
                    message=message,
                    execution_time=execution_time,
                )

            return {
                'status': status_label,
                'message': message,
                'execution_time': execution_time,
                'http_status': response.status_code,
            }
        except requests.RequestException as exc:
            execution_time = time.time() - start
            logger.error('n8n trigger failed for %s: %s', workflow.slug, exc)

            log_farm = farm or resolve_log_farm(
                workflow.organization_id,
                farm_id=farm.id if farm else None,
                workflow_farm=workflow.farm,
            )
            if log_farm:
                IntegrationLog.objects.create(
                    farm=log_farm,
                    integration_type='n8n',
                    action=f"{'test_' if test_mode else ''}{workflow.slug}",
                    status='failed',
                    message=str(exc),
                    execution_time=execution_time,
                )

            return {
                'status': 'failed',
                'message': str(exc),
                'execution_time': execution_time,
                'http_status': None,
            }
