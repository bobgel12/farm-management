from django.core.management.base import BaseCommand

from analytics.services import ensure_farm_dashboard
from farms.models import Farm


class Command(BaseCommand):
    help = "Create missing farm BI dashboards for existing farms"

    def handle(self, *args, **options):
        created_or_ensured = 0
        skipped = 0

        farms = Farm.objects.select_related('organization').all()
        for farm in farms:
            if farm.organization_id is None:
                skipped += 1
                continue
            users_qs = farm.organization.organization_users.filter(is_active=True).select_related('user')
            org_user = users_qs.first()
            if org_user is None:
                skipped += 1
                continue
            ensure_farm_dashboard(farm, org_user.user)
            created_or_ensured += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Farm dashboards ensured: {created_or_ensured}. Skipped farms: {skipped}."
            )
        )
