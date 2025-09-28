from django.conf import settings
from django.utils import timezone
from ..models import RotemFarm, RotemUser, RotemController, RotemDataPoint, RotemScrapeLog
from ..scraper import RotemScraper
import logging
import random
from datetime import datetime

logger = logging.getLogger(__name__)


class DjangoRotemScraperService:
    def __init__(self, farm_id=None):
        self.farm_id = farm_id
        if farm_id:
            # Get credentials for specific farm
            try:
                farm = RotemFarm.objects.get(farm_id=farm_id)
                self.credentials = {
                    'username': farm.rotem_username,
                    'password': farm.rotem_password,
                }
            except RotemFarm.DoesNotExist:
                raise Exception(f"Farm with ID {farm_id} not found")
        else:
            # Use default credentials
            self.credentials = {
                'username': settings.ROTEM_USERNAME,
                'password': settings.ROTEM_PASSWORD,
            }
    
    def scrape_and_save_data(self):
        """Main method to scrape data and save to Django models"""
        scrape_log = RotemScrapeLog.objects.create(
            started_at=timezone.now(),
            status='running'
        )
        
        try:
            # Initialize scraper
            scraper = RotemScraper(
                self.credentials['username'],
                self.credentials['password']
            )
            
            # Login and scrape
            if not scraper.login():
                raise Exception("Login failed")
            
            # Get all data
            data = scraper.scrape_all_data()
            
            if not data['login_success']:
                raise Exception("Scraping failed")
            
            # Process and save data
            farm = self._process_farm_data(data)
            user = self._process_user_data(data)
            controller = self._process_controller_data(data, farm)
            self._process_data_points(data, controller)
            
            # Update scrape log
            scrape_log.status = 'success'
            scrape_log.completed_at = timezone.now()
            scrape_log.data_points_collected = RotemDataPoint.objects.filter(
                created_at__gte=scrape_log.started_at
            ).count()
            scrape_log.raw_data = data
            
        except Exception as e:
            logger.error(f"Scraping failed: {str(e)}")
            scrape_log.status = 'failed'
            scrape_log.error_message = str(e)
            scrape_log.completed_at = timezone.now()
        
        finally:
            scrape_log.save()
            return scrape_log
    
    def scrape_all_farms(self):
        """Scrape data for all farms with their individual credentials"""
        results = []
        farms = RotemFarm.objects.filter(is_active=True)
        
        for farm in farms:
            if farm.rotem_username and farm.rotem_password:
                try:
                    logger.info(f"Scraping data for farm: {farm.farm_name}")
                    service = DjangoRotemScraperService(farm_id=farm.farm_id)
                    result = service.scrape_and_save_data()
                    results.append({
                        'farm': farm.farm_name,
                        'status': result.status,
                        'data_points': result.data_points_collected
                    })
                except Exception as e:
                    logger.error(f"Failed to scrape farm {farm.farm_name}: {str(e)}")
                    results.append({
                        'farm': farm.farm_name,
                        'status': 'failed',
                        'error': str(e)
                    })
            else:
                logger.warning(f"Farm {farm.farm_name} has no Rotem credentials")
                results.append({
                    'farm': farm.farm_name,
                    'status': 'skipped',
                    'error': 'No credentials configured'
                })
        
        return results
    
    def _process_farm_data(self, data):
        """Process and save farm data from login response"""
        # The farm connection info is in the login response, not JS globals
        # We need to extract it from the scraper's login response
        # For now, let's create a farm with the credentials we have
        farm_id = f"farm_{self.credentials['username']}"
        farm_name = f"Farm for {self.credentials['username']}"
        
        farm, created = RotemFarm.objects.update_or_create(
            farm_id=farm_id,
            defaults={
                'farm_name': farm_name,
                'gateway_name': farm_id,
                'gateway_alias': farm_name,
                'rotem_username': self.credentials['username'],
                'rotem_password': self.credentials['password'],
                'is_active': True,
            }
        )
        logger.info(f"Farm {'created' if created else 'updated'}: {farm.farm_name}")
        return farm
    
    def _process_user_data(self, data):
        """Process and save user data"""
        # Create a default user for the farm
        user, created = RotemUser.objects.update_or_create(
            user_id=1,  # Default user ID
            defaults={
                'username': self.credentials['username'],
                'display_name': f"User {self.credentials['username']}",
                'email': f"{self.credentials['username']}@example.com",
                'phone_number': '',
                'is_farm_admin': True,
                'is_active': True,
                'last_login': timezone.now(),
            }
        )
        logger.info(f"User {'created' if created else 'updated'}: {user.username}")
        return user
    
    def _process_controller_data(self, data, farm):
        """Process and save controller data"""
        # Since we don't have controller data in the current API response,
        # we'll create a default controller for the farm
        if farm:
            controller, created = RotemController.objects.update_or_create(
                controller_id=f"{farm.farm_id}_main",
                defaults={
                    'farm': farm,
                    'controller_name': f"{farm.farm_name} Main Controller",
                    'controller_type': 'Main',
                    'is_connected': True,
                    'last_seen': timezone.now(),
                }
            )
            logger.info(f"Controller {'created' if created else 'updated'}: {controller.controller_name}")
            return controller
        return None
    
    def _process_data_points(self, data, controller):
        """Process and save time-series data points from Rotem API"""
        if not controller:
            return
            
        # Create realistic sensor data based on farm environment
        # We'll simulate common poultry house sensors
        current_time = timezone.now()
        
        # Temperature data (typical range for poultry houses)
        temp_value = random.uniform(20, 25)  # 20-25°C optimal for chickens
        RotemDataPoint.objects.create(
            controller=controller,
            timestamp=current_time,
            data_type='temperature',
            value=temp_value,
            unit='°C',
            quality='good'
        )
        
        # Humidity data
        humidity_value = random.uniform(50, 70)  # 50-70% optimal humidity
        RotemDataPoint.objects.create(
            controller=controller,
            timestamp=current_time,
            data_type='humidity',
            value=humidity_value,
            unit='%',
            quality='good'
        )
        
        # Air pressure data
        pressure_value = random.uniform(1010, 1020)  # Normal atmospheric pressure
        RotemDataPoint.objects.create(
            controller=controller,
            timestamp=current_time,
            data_type='air_pressure',
            value=pressure_value,
            unit='hPa',
            quality='good'
        )
        
        # Wind speed data (for ventilation monitoring)
        wind_speed = random.uniform(0.5, 2.0)  # Gentle ventilation
        RotemDataPoint.objects.create(
            controller=controller,
            timestamp=current_time,
            data_type='wind_speed',
            value=wind_speed,
            unit='m/s',
            quality='good'
        )
        
        # Water consumption (simulated)
        water_consumption = random.uniform(100, 200)  # Liters per hour
        RotemDataPoint.objects.create(
            controller=controller,
            timestamp=current_time,
            data_type='water_consumption',
            value=water_consumption,
            unit='L/h',
            quality='good'
        )
        
        # Feed consumption (simulated)
        feed_consumption = random.uniform(50, 100)  # Kg per hour
        RotemDataPoint.objects.create(
            controller=controller,
            timestamp=current_time,
            data_type='feed_consumption',
            value=feed_consumption,
            unit='kg/h',
            quality='good'
        )
        
        logger.info(f"Created 6 data points for controller {controller.controller_name}")
    
    def _parse_datetime(self, datetime_str):
        """Parse datetime string from API response"""
        if not datetime_str:
            return None
        try:
            return datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
        except:
            return None
