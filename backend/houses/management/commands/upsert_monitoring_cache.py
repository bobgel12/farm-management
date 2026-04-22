from django.core.management.base import BaseCommand

from houses.services.monitoring_cache_service import upsert_monitoring_cache_for_all_farms


class Command(BaseCommand):
    help = "Upsert cached Rotem monitoring payloads for all active integrated farms."

    def handle(self, *args, **options):
        result = upsert_monitoring_cache_for_all_farms()
        self.stdout.write(
            self.style.SUCCESS(
                f"status={result.status} farms_processed={result.farms_processed} houses_processed={result.houses_processed}"
            )
        )
        if result.message:
            self.stdout.write(self.style.WARNING(result.message))
