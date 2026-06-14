import logging

from django.db import models
from django.shortcuts import get_object_or_404
from farms.models import Farm
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import AutomationWorkflow
from .n8n import N8nTriggerService, resolve_workflow
from .permissions import user_accessible_organization_ids, user_can_access_organization, user_is_org_admin
from .serializers import (
    AutomationTriggerSerializer,
    AutomationWorkflowAdminSerializer,
    AutomationWorkflowListSerializer,
)

logger = logging.getLogger(__name__)


class AutomationWorkflowViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = AutomationWorkflow.objects.select_related('organization', 'farm')
        org_ids = user_accessible_organization_ids(self.request.user)
        if org_ids is not None:
            queryset = queryset.filter(organization_id__in=org_ids)

        organization_id = self.request.query_params.get('organization_id')
        if organization_id:
            queryset = queryset.filter(organization_id=organization_id)

        farm_id = self.request.query_params.get('farm_id')
        if farm_id:
            queryset = queryset.filter(models.Q(farm_id=farm_id) | models.Q(farm__isnull=True))

        return queryset.order_by('name')

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return AutomationWorkflowAdminSerializer
        return AutomationWorkflowListSerializer

    def _check_org_admin(self, organization_id):
        if not user_is_org_admin(self.request.user, organization_id):
            return Response(
                {'error': 'You do not have permission to manage automation workflows'},
                status=status.HTTP_403_FORBIDDEN,
            )
        return None

    def create(self, request, *args, **kwargs):
        organization_id = request.data.get('organization')
        if not organization_id:
            return Response(
                {'error': 'organization is required'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        denied = self._check_org_admin(organization_id)
        if denied:
            return denied
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        denied = self._check_org_admin(instance.organization_id)
        if denied:
            return denied
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        denied = self._check_org_admin(instance.organization_id)
        if denied:
            return denied
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        denied = self._check_org_admin(instance.organization_id)
        if denied:
            return denied
        return super().destroy(request, *args, **kwargs)

    @action(detail=False, methods=['post'], url_path=r'(?P<workflow_slug>[-\w]+)/trigger')
    def trigger(self, request, workflow_slug=None):
        serializer = AutomationTriggerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        organization_id = data.get('organization_id')
        farm_id = data.get('farm_id')
        extra_payload = data.get('payload', {})

        if not organization_id and farm_id:
            farm = get_object_or_404(Farm, id=farm_id)
            organization_id = farm.organization_id

        if not organization_id:
            return Response(
                {'error': 'organization_id or farm_id is required'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not user_can_access_organization(request.user, organization_id):
            return Response(
                {'error': 'You do not have access to this organization'},
                status=status.HTTP_403_FORBIDDEN,
            )

        workflow = resolve_workflow(organization_id, workflow_slug, farm_id=farm_id)
        if not workflow:
            return Response(
                {'error': f'Workflow "{workflow_slug}" not found'},
                status=status.HTTP_404_NOT_FOUND,
            )

        farm = None
        if farm_id:
            farm = get_object_or_404(Farm, id=farm_id, organization_id=organization_id)

        service = N8nTriggerService()
        result = service.trigger(workflow, request.user, farm=farm, extra_payload=extra_payload)

        http_status = (
            status.HTTP_200_OK
            if result['status'] == 'success'
            else status.HTTP_502_BAD_GATEWAY
        )
        return Response(
            {
                'status': result['status'],
                'message': result['message'],
                'execution_time': result['execution_time'],
                'workflow_slug': workflow_slug,
            },
            status=http_status,
        )

    @action(detail=False, methods=['post'], url_path=r'(?P<workflow_slug>[-\w]+)/test')
    def test(self, request, workflow_slug=None):
        serializer = AutomationTriggerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        organization_id = data.get('organization_id')
        farm_id = data.get('farm_id')

        if not organization_id and farm_id:
            farm = get_object_or_404(Farm, id=farm_id)
            organization_id = farm.organization_id

        if not organization_id:
            return Response(
                {'error': 'organization_id or farm_id is required'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not user_is_org_admin(request.user, organization_id):
            return Response(
                {'error': 'Only organization admins can test workflows'},
                status=status.HTTP_403_FORBIDDEN,
            )

        workflow = resolve_workflow(organization_id, workflow_slug, farm_id=farm_id)
        if not workflow:
            return Response(
                {'error': f'Workflow "{workflow_slug}" not found'},
                status=status.HTTP_404_NOT_FOUND,
            )

        farm = None
        if farm_id:
            farm = get_object_or_404(Farm, id=farm_id, organization_id=organization_id)

        service = N8nTriggerService()
        result = service.trigger(
            workflow,
            request.user,
            farm=farm,
            extra_payload={'test': True},
            test_mode=True,
        )

        http_status = (
            status.HTTP_200_OK
            if result['status'] == 'success'
            else status.HTTP_502_BAD_GATEWAY
        )
        return Response(
            {
                'status': result['status'],
                'message': result['message'],
                'execution_time': result['execution_time'],
                'workflow_slug': workflow_slug,
            },
            status=http_status,
        )
