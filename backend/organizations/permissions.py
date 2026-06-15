from organizations.models import OrganizationUser


def user_accessible_organization_ids(user):
    if not user.is_authenticated:
        return []
    if user.is_staff:
        return None
    return list(
        OrganizationUser.objects.filter(user=user, is_active=True).values_list(
            'organization_id', flat=True
        )
    )


def user_can_access_organization(user, organization_id) -> bool:
    if user.is_staff:
        return True
    return OrganizationUser.objects.filter(
        organization_id=organization_id,
        user=user,
        is_active=True,
    ).exists()


def user_is_org_admin(user, organization_id) -> bool:
    if user.is_staff:
        return True
    if organization_id is None:
        return False
    return OrganizationUser.objects.filter(
        organization_id=organization_id,
        user=user,
        is_active=True,
        role__in=['owner', 'admin'],
    ).exists()
