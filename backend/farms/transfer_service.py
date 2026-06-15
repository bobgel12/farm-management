from django.db import transaction

from analytics.models import Dashboard
from analytics.services import ensure_farm_dashboard
from integrations.models import AutomationWorkflow
from organizations.models import Organization


class FarmTransferError(Exception):
    def __init__(self, message, code='transfer_error'):
        self.message = message
        self.code = code
        super().__init__(message)


class FarmTransferService:
    @staticmethod
    @transaction.atomic
    def transfer(farm, target_org: Organization, actor):
        if farm.organization_id is None:
            raise FarmTransferError(
                'Farm has no organization assigned',
                code='no_source_organization',
            )

        if farm.organization_id == target_org.id:
            raise FarmTransferError(
                'Farm already belongs to this organization',
                code='same_organization',
            )

        if not target_org.can_add_farm():
            raise FarmTransferError(
                f'Target organization has reached its farm limit ({target_org.max_farms})',
                code='farm_limit_reached',
            )

        previous_organization_id = farm.organization_id

        dashboards_updated = Dashboard.objects.filter(
            farm=farm,
            dashboard_type='farm',
        ).update(organization=target_org)

        automation_workflows_updated = AutomationWorkflow.objects.filter(
            farm=farm,
        ).update(organization=target_org)

        farm.organization = target_org
        farm.save(update_fields=['organization', 'updated_at'])

        ensure_farm_dashboard(farm, actor)

        return {
            'farm_id': farm.id,
            'previous_organization_id': str(previous_organization_id),
            'organization_id': str(target_org.id),
            'dashboards_updated': dashboards_updated,
            'automation_workflows_updated': automation_workflows_updated,
        }
