from django.core.management.base import BaseCommand
from rotem_scraper.services.scraper_service import DjangoRotemScraperService
from rotem_scraper.models import RotemFarm, RotemDataPoint, RotemController


class Command(BaseCommand):
    help = 'Test the Rotem scraper service'

    def add_arguments(self, parser):
        parser.add_argument('--farm-id', type=str, help='Test specific farm by ID')
        parser.add_argument('--all-farms', action='store_true', help='Test all farms')

    def handle(self, *args, **options):
        farm_id = options.get('farm_id')
        all_farms = options.get('all_farms', False)
        
        if all_farms:
            self.stdout.write('Testing Rotem scraper for all farms...')
            service = DjangoRotemScraperService()
            results = service.scrape_all_farms()
            
            for result in results:
                if result['status'] == 'success':
                    self.stdout.write(
                        self.style.SUCCESS(f"✓ {result['farm']}: {result['data_points']} data points")
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(f"✗ {result['farm']}: {result.get('error', 'Unknown error')}")
                    )
        else:
            self.stdout.write(f'Testing Rotem scraper for farm: {farm_id or "default"}...')
            
            try:
                service = DjangoRotemScraperService(farm_id=farm_id)
                result = service.scrape_and_save_data()
                
                self.stdout.write(
                    self.style.SUCCESS(f'Scraping completed with status: {result.status}')
                )
                self.stdout.write(f'Data points collected: {result.data_points_collected}')
                
                if result.error_message:
                    self.stdout.write(
                        self.style.WARNING(f'Error message: {result.error_message}')
                    )
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Scraping failed: {str(e)}')
                )
        
        # Show current data counts
        self.stdout.write('\n=== Current Data Counts ===')
        self.stdout.write(f'Farms: {RotemFarm.objects.count()}')
        self.stdout.write(f'Controllers: {RotemController.objects.count()}')
        self.stdout.write(f'Data Points: {RotemDataPoint.objects.count()}')
        
        # Show recent data points
        recent_points = RotemDataPoint.objects.order_by('-timestamp')[:5]
        if recent_points:
            self.stdout.write('\n=== Recent Data Points ===')
            for point in recent_points:
                self.stdout.write(f'{point.controller.controller_name}: {point.data_type} = {point.value} {point.unit} at {point.timestamp}')
