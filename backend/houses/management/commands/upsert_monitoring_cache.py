from django.core.management.base import BaseCommand

from houses.services.monitoring_cache_run_service import (
    create_scheduled_refresh_run,
    execute_refresh_run,
)


class Command(BaseCommand):
    help = "Upsert cached Rotem monitoring payloads for all active integrated farms."

    def handle(self, *args, **options):
        run = execute_refresh_run(create_scheduled_refresh_run())
        self.stdout.write(
            self.style.SUCCESS(
                f"status={run.status} farms_processed={run.farms_processed} houses_processed={run.houses_processed} run_id={run.run_id}"
            )
        )
        if run.error_summary:
            self.stdout.write(self.style.WARNING(run.error_summary))
