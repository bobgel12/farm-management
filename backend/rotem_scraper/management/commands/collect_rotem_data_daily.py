from django.core.management.base import BaseCommand
from django.utils import timezone
from rotem_scraper.services.scraper_service import DjangoRotemScraperService
from rotem_scraper.services.aggregation_service import RotemAggregationService
from rotem_scraper.models import RotemFarm
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Collect Rotem API data daily and persist for analytics'

    def add_arguments(self, parser):
        parser.add_argument(
            '--farm-id',
            type=str,
            help='Collect data for specific farm ID (optional)',
        )
        parser.add_argument(
            '--all-farms',
            action='store_true',
            help='Collect data for all active farms (default behavior)',
        )

    def handle(self, *args, **options):
        farm_id = options.get('farm_id')
        
        self.stdout.write(
            self.style.SUCCESS('Starting daily Rotem data collection...')
        )
        
        try:
            if farm_id:
                # Collect data for specific farm
                self.stdout.write(f'Collecting data for farm: {farm_id}')
                
                try:
                    farm = RotemFarm.objects.get(farm_id=farm_id)
                    if not farm.is_active:
                        self.stdout.write(
                            self.style.WARNING(f'Farm {farm_id} is not active. Skipping.')
                        )
                        return
                except RotemFarm.DoesNotExist:
                    self.stdout.write(
                        self.style.ERROR(f'Farm with ID {farm_id} not found')
                    )
                    return
                
                service = DjangoRotemScraperService(farm_id=farm_id)
                scrape_log = service.scrape_and_save_data()
                
                if scrape_log.status == 'success':
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✅ Successfully collected {scrape_log.data_points_collected} data points for farm {farm_id}'
                        )
                    )
                    
                    # Aggregate data for yesterday (data collection happens daily)
                    self.stdout.write('Aggregating data into daily summaries...')
                    try:
                        from rotem_scraper.models import RotemController
                        controllers = RotemController.objects.filter(farm=farm)
                        for controller in controllers:
                            RotemAggregationService.aggregate_daily_data(
                                controller,
                                target_date=(timezone.now() - timezone.timedelta(days=1)).date()
                            )
                        self.stdout.write(self.style.SUCCESS('✅ Data aggregation completed'))
                    except Exception as e:
                        self.stdout.write(
                            self.style.WARNING(f'⚠️  Data aggregation failed: {str(e)}')
                        )
                else:
                    self.stdout.write(
                        self.style.ERROR(
                            f'❌ Data collection failed for farm {farm_id}: {scrape_log.error_message}'
                        )
                    )
            else:
                # Collect data for all active farms
                active_farms = RotemFarm.objects.filter(is_active=True)
                total_farms = active_farms.count()
                
                self.stdout.write(f'Collecting data for {total_farms} active farms...')
                
                service = DjangoRotemScraperService()
                results = service.scrape_all_farms()
                
                successful_farms = [r for r in results if r.get('status') == 'success']
                failed_farms = [r for r in results if r.get('status') != 'success']
                
                total_data_points = sum(r.get('data_points_collected', 0) for r in results)
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ Data collection completed:'
                    )
                )
                self.stdout.write(f'   - Total farms processed: {len(results)}')
                self.stdout.write(f'   - Successful: {len(successful_farms)}')
                self.stdout.write(f'   - Failed: {len(failed_farms)}')
                self.stdout.write(f'   - Total data points collected: {total_data_points}')
                
                if failed_farms:
                    self.stdout.write(
                        self.style.WARNING('Failed farms:')
                    )
                    for result in failed_farms:
                        self.stdout.write(
                            f'   - {result.get("farm_id", "Unknown")}: {result.get("error", "Unknown error")}'
                        )
                
                # Aggregate data for yesterday for all successful farms
                if successful_farms:
                    self.stdout.write('Aggregating data into daily summaries...')
                    try:
                        agg_results = RotemAggregationService.aggregate_all_controllers_for_date(
                            target_date=(timezone.now() - timezone.timedelta(days=1)).date()
                        )
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'✅ Data aggregation completed: {agg_results["summaries_created"]} summaries created'
                            )
                        )
                    except Exception as e:
                        self.stdout.write(
                            self.style.WARNING(f'⚠️  Data aggregation failed: {str(e)}')
                        )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error during daily data collection: {str(e)}')
            )
            logger.error(f'Error in daily Rotem data collection: {str(e)}', exc_info=True)
            raise

