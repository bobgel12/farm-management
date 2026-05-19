"""Management command to backfill HouseDailySummary and RotemDailySummary."""
from django.core.management.base import BaseCommand

from rotem_scraper.tasks import backfill_daily_summaries


class Command(BaseCommand):
    help = 'Backfill per-house daily summaries and sync controller-level RotemDailySummary'

    def add_arguments(self, parser):
        parser.add_argument('--days', type=int, default=7, help='Number of days to backfill')
        parser.add_argument(
            '--no-force',
            action='store_true',
            help='Skip updating existing summary rows',
        )

    def handle(self, *args, **options):
        days = options['days']
        force = not options['no_force']
        result = backfill_daily_summaries(days=days, force_update=force)
        self.stdout.write(self.style.SUCCESS(f'Backfill complete: {result}'))
