from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from django.db import transaction
from .models import Organization, OrganizationUser
from .serializers import (
    OrganizationSerializer,
    OrganizationListSerializer,
    OrganizationUserSerializer,
    OrganizationMembershipSerializer
)


class OrganizationViewSet(viewsets.ModelViewSet):
    """ViewSet for Organization management"""
    queryset = Organization.objects.all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return OrganizationListSerializer
        return OrganizationSerializer
    
    def get_queryset(self):
        """Filter organizations based on user's memberships"""
        if self.request.user.is_staff:
            return Organization.objects.all()
        
        # Get organizations where user is a member
        user_organizations = Organization.objects.filter(
            organization_users__user=self.request.user,
            organization_users__is_active=True
        ).distinct()
        
        return user_organizations
    
    def perform_create(self, serializer):
        """Set created_by when creating organization"""
        with transaction.atomic():
            organization = serializer.save(created_by=self.request.user)
            # Create owner membership (handled by signal, but ensure it exists)
            if not OrganizationUser.objects.filter(organization=organization, user=self.request.user).exists():
                OrganizationUser.objects.create(
                    organization=organization,
                    user=self.request.user,
                    role='owner',
                    can_manage_farms=True,
                    can_manage_users=True,
                    can_view_reports=True,
                    can_export_data=True,
                    invited_by=self.request.user
                )
    
    @action(detail=True, methods=['get'])
    def members(self, request, pk=None):
        """Get all members of an organization"""
        organization = self.get_object()
        
        # Check permission
        membership = OrganizationUser.objects.filter(
            organization=organization,
            user=request.user,
            is_active=True
        ).first()
        
        if not membership or not (membership.is_admin or request.user.is_staff):
            return Response(
                {'error': 'You do not have permission to view members'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        members = OrganizationUser.objects.filter(organization=organization, is_active=True)
        serializer = OrganizationUserSerializer(members, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def add_member(self, request, pk=None):
        """Add a member to the organization"""
        organization = self.get_object()
        
        # Check permission
        membership = OrganizationUser.objects.filter(
            organization=organization,
            user=request.user,
            is_active=True
        ).first()
        
        if not membership or not membership.can_manage_users:
            return Response(
                {'error': 'You do not have permission to add members'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        user_id = request.data.get('user_id')
        if not user_id:
            return Response(
                {'error': 'user_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if user is already a member
        if OrganizationUser.objects.filter(organization=organization, user=user).exists():
            return Response(
                {'error': 'User is already a member of this organization'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check organization user limit
        if not organization.can_add_user():
            return Response(
                {'error': 'Organization has reached maximum user limit'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create membership
        role = request.data.get('role', 'worker')
        org_user = OrganizationUser.objects.create(
            organization=organization,
            user=user,
            role=role,
            invited_by=request.user,
            can_manage_farms=request.data.get('can_manage_farms', False),
            can_manage_users=request.data.get('can_manage_users', False),
            can_view_reports=request.data.get('can_view_reports', True),
            can_export_data=request.data.get('can_export_data', False),
        )
        
        serializer = OrganizationUserSerializer(org_user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['delete'])
    def remove_member(self, request, pk=None):
        """Remove a member from the organization"""
        organization = self.get_object()
        
        # Check permission
        membership = OrganizationUser.objects.filter(
            organization=organization,
            user=request.user,
            is_active=True
        ).first()
        
        if not membership or not membership.can_manage_users:
            return Response(
                {'error': 'You do not have permission to remove members'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        user_id = request.data.get('user_id')
        if not user_id:
            return Response(
                {'error': 'user_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            org_user = OrganizationUser.objects.get(
                organization=organization,
                user_id=user_id
            )
        except OrganizationUser.DoesNotExist:
            return Response(
                {'error': 'User is not a member of this organization'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Prevent removing the owner
        if org_user.role == 'owner':
            return Response(
                {'error': 'Cannot remove organization owner'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        org_user.delete()
        return Response({'message': 'Member removed successfully'}, status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=False, methods=['get'])
    def my_organizations(self, request):
        """Get all organizations the current user belongs to"""
        memberships = OrganizationUser.objects.filter(
            user=request.user,
            is_active=True
        ).select_related('organization')
        
        serializer = OrganizationMembershipSerializer(memberships, many=True)
        return Response(serializer.data)


class OrganizationUserViewSet(viewsets.ModelViewSet):
    """ViewSet for OrganizationUser management"""
    queryset = OrganizationUser.objects.all()
    serializer_class = OrganizationUserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter based on user's organization memberships"""
        if self.request.user.is_staff:
            return OrganizationUser.objects.all()
        
        # Get memberships in organizations where user is admin
        user_organizations = Organization.objects.filter(
            organization_users__user=self.request.user,
            organization_users__is_active=True,
            organization_users__can_manage_users=True
        ).distinct()
        
        return OrganizationUser.objects.filter(organization__in=user_organizations)
    
    def update(self, request, *args, **kwargs):
        """Update organization user with permission check"""
        instance = self.get_object()
        
        # Check if user has permission to modify this membership
        user_membership = OrganizationUser.objects.filter(
            organization=instance.organization,
            user=request.user,
            is_active=True
        ).first()
        
        if not user_membership or not user_membership.can_manage_users:
            return Response(
                {'error': 'You do not have permission to modify members'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Prevent changing owner role
        if 'role' in request.data and instance.role == 'owner':
            return Response(
                {'error': 'Cannot change owner role'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return super().update(request, *args, **kwargs)

