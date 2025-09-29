import time
from typing import Dict, Any
from django.utils import timezone
from rotem_scraper.scraper import RotemScraper
from rotem_scraper.services.scraper_service import DjangoRotemScraperService
from .base import FarmSystemIntegration
from .models import IntegrationError


class RotemIntegration(FarmSystemIntegration):
    """Rotem system integration implementation"""
    
    def __init__(self, farm):
        super().__init__(farm)
        self.scraper = None
        self.scraper_service = None
        self._initialize_scraper()
    
    def get_integration_type(self) -> str:
        return 'rotem'
    
    def _initialize_scraper(self):
        """Initialize Rotem scraper with farm credentials"""
        if not self.farm.rotem_username or not self.farm.rotem_password:
            raise ValueError("Rotem credentials not configured for this farm")
        
        self.scraper = RotemScraper(
            username=self.farm.rotem_username,
            password=self.farm.rotem_password
        )
        self.scraper_service = DjangoRotemScraperService()
    
    def test_connection(self) -> bool:
        """Test if Rotem system is accessible"""
        try:
            start_time = time.time()
            success = self.scraper.login()
            execution_time = time.time() - start_time
            
            if success:
                self.log_activity(
                    action='test_connection',
                    status='success',
                    message='Successfully connected to Rotem system',
                    execution_time=execution_time
                )
                self.update_health(is_healthy=True, response_time=execution_time)
            else:
                self.log_activity(
                    action='test_connection',
                    status='failed',
                    message='Failed to connect to Rotem system',
                    execution_time=execution_time
                )
                self.update_health(is_healthy=False)
            
            return success
            
        except Exception as e:
            error = IntegrationError.objects.create(
                farm=self.farm,
                integration_type=self.integration_type,
                error_type='connection',
                error_message=str(e),
                error_code='CONNECTION_FAILED'
            )
            self.log_activity(
                action='test_connection',
                status='failed',
                message=f'Connection test failed: {str(e)}'
            )
            self.update_health(is_healthy=False, last_error=error)
            return False
    
    def sync_house_data(self, farm_id: str) -> Dict[str, Any]:
        """Sync house data from Rotem system"""
        try:
            start_time = time.time()
            
            # Use the existing scraper service to get data
            data = self.scraper_service.scrape_farm_data(self.farm)
            
            execution_time = time.time() - start_time
            data_points = len(data.get('houses', []))
            
            self.log_activity(
                action='sync_house_data',
                status='success',
                message=f'Successfully synced {data_points} houses',
                data_points=data_points,
                execution_time=execution_time
            )
            self.update_health(is_healthy=True, response_time=execution_time)
            
            return data
            
        except Exception as e:
            error = IntegrationError.objects.create(
                farm=self.farm,
                integration_type=self.integration_type,
                error_type='data_sync',
                error_message=str(e),
                error_code='SYNC_FAILED'
            )
            self.log_activity(
                action='sync_house_data',
                status='failed',
                message=f'Data sync failed: {str(e)}'
            )
            self.update_health(is_healthy=False, last_error=error)
            return {}
    
    def get_house_count(self, farm_id: str) -> int:
        """Get number of houses from Rotem system"""
        try:
            # Rotem typically has 8 houses
            # In a real implementation, this would query the system
            return 8
        except Exception as e:
            self.log_error('data_query', f'Failed to get house count: {str(e)}')
            return 0
    
    def get_house_age(self, farm_id: str, house_number: int) -> int:
        """Get house age in days from Rotem data"""
        try:
            # This would query the specific house data from Rotem
            # For now, return a default value
            return 0
        except Exception as e:
            self.log_error('data_query', f'Failed to get house age for house {house_number}: {str(e)}')
            return 0
    
    def get_sensor_data(self, house_number: int) -> Dict[str, Any]:
        """Get real-time sensor data for a specific house"""
        try:
            start_time = time.time()
            
            # Ensure scraper is logged in before making API calls
            if not self.scraper.user_token:
                login_success = self.scraper.login()
                if not login_success:
                    raise Exception("Failed to login to Rotem system")
            
            # Use the scraper to get command data for the house
            command_data = self.scraper.get_command_data(house_number)
            
            execution_time = time.time() - start_time
            
            self.log_activity(
                action='get_sensor_data',
                status='success',
                message=f'Retrieved sensor data for house {house_number}',
                execution_time=execution_time
            )
            
            return command_data
            
        except Exception as e:
            error = IntegrationError.objects.create(
                farm=self.farm,
                integration_type=self.integration_type,
                error_type='sensor_data',
                error_message=f'Failed to get sensor data for house {house_number}: {str(e)}',
                error_code='SENSOR_DATA_FAILED'
            )
            self.log_activity(
                action='get_sensor_data',
                status='failed',
                message=f'Failed to get sensor data for house {house_number}: {str(e)}'
            )
            self.update_health(is_healthy=False, last_error=error)
            return {}
    
    def get_all_sensor_data(self) -> Dict[str, Any]:
        """Get real-time sensor data for all houses"""
        try:
            start_time = time.time()
            
            # Get data for all 8 houses
            all_data = {}
            for house_num in range(1, 9):
                house_data = self.get_sensor_data(house_num)
                if house_data:
                    all_data[f'house_{house_num}'] = house_data
            
            execution_time = time.time() - start_time
            
            self.log_activity(
                action='get_all_sensor_data',
                status='success',
                message=f'Retrieved sensor data for {len(all_data)} houses',
                data_points=len(all_data),
                execution_time=execution_time
            )
            
            return all_data
            
        except Exception as e:
            error = IntegrationError.objects.create(
                farm=self.farm,
                integration_type=self.integration_type,
                error_type='sensor_data',
                error_message=f'Failed to get all sensor data: {str(e)}',
                error_code='ALL_SENSOR_DATA_FAILED'
            )
            self.log_activity(
                action='get_all_sensor_data',
                status='failed',
                message=f'Failed to get all sensor data: {str(e)}'
            )
            self.update_health(is_healthy=False, last_error=error)
            return {}
