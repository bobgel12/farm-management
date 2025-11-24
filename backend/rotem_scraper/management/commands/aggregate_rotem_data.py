from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date, timedelta
from rotem_scraper.services.aggregation_service import RotemAggregationService
from rotem_scraper.models import RotemController
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Aggregate Rotem data points into daily summaries for analytics and ML'

    def add_arguments(self, parser):
        parser.add_argument(
            '--date',
            type=str,
            help='Date to aggregate (YYYY-MM-DD). Defaults to yesterday.',
        )
        parser.add_argument(
            '--days',
            type=int,
            help='Number of days to aggregate (from today backwards). Default: 1',
        )
        parser.add_argument(
            '--controller-id',
            type=int,
            help='Aggregate data for specific controller ID only',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force update existing summaries',
        )

    def handle(self, *args, **options):
        target_date_str = options.get('date')
        days = options.get('days', 1)
        controller_id = options.get('controller_id')
        force_update = options.get('force', False)
        
        self.stdout.write(
            self.style.SUCCESS('Starting Rotem data aggregation...')
        )
        
        try:
            if controller_id:
                # Aggregate for specific controller
                try:
                    controller = RotemController.objects.get(id=controller_id)
                    self.stdout.write(f'Aggregating data for controller: {controller.controller_name}')
                    
                    if target_date_str:
                        target_date = date.fromisoformat(target_date_str)
                        summary = RotemAggregationService.aggregate_daily_data(
                            controller, target_date, force_update
                        )
                        if summary:
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f'✅ Created/updated summary for {controller.controller_name} on {target_date}'
                                )
                            )
                        else:
                            self.stdout.write(
                                self.style.WARNING(
                                    f'⚠️  No data points found for {controller.controller_name} on {target_date}'
                                )
                            )
                    else:
                        # Aggregate last N days
                        end_date = (timezone.now() - timedelta(days=1)).date()
                        start_date = end_date - timedelta(days=days - 1)
                        
                        summaries = RotemAggregationService.aggregate_controller_range(
                            controller, start_date, end_date, force_update
                        )
                        
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'✅ Created/updated {len(summaries)} summaries for {controller.controller_name}'
                            )
                        )
                except RotemController.DoesNotExist:
                    self.stdout.write(
                        self.style.ERROR(f'Controller with ID {controller_id} not found')
                    )
                    return
            else:
                # Aggregate for all controllers
                if target_date_str:
                    target_date = date.fromisoformat(target_date_str)
                    self.stdout.write(f'Aggregating data for date: {target_date}')
                    
                    results = RotemAggregationService.aggregate_all_controllers_for_date(
                        target_date, force_update
                    )
                    
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✅ Aggregation completed for {target_date}:'
                        )
                    )
                    self.stdout.write(f'   - Controllers processed: {results["total_controllers"]}')
                    self.stdout.write(f'   - Successful: {results["successful"]}')
                    self.stdout.write(f'   - Failed: {results["failed"]}')
                    self.stdout.write(f'   - Summaries created: {results["summaries_created"]}')
                    self.stdout.write(f'   - Summaries updated: {results["summaries_updated"]}')
                else:
                    # Aggregate last N days for all controllers
                    self.stdout.write(f'Aggregating data for last {days} days...')
                    
                    results = RotemAggregationService.aggregate_recent_days(days, force_update)
                    
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✅ Aggregation completed:'
                        )
                    )
                    self.stdout.write(f'   - Date range: {results["start_date"]} to {results["end_date"]}')
                    self.stdout.write(f'   - Days processed: {results["days_processed"]}')
                    self.stdout.write(f'   - Total summaries: {results["total_summaries"]}')
                    
        except ValueError as e:
            self.stdout.write(
                self.style.ERROR(f'Invalid date format: {str(e)}. Use YYYY-MM-DD format.')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error during aggregation: {str(e)}')
            )
            logger.error(f'Error in Rotem data aggregation: {str(e)}', exc_info=True)
            raise

