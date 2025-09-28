from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from django.utils import timezone
from .models import IntegrationLog, IntegrationError, IntegrationHealth


class FarmSystemIntegration(ABC):
    """Base class for farm system integrations"""
    
    def __init__(self, farm):
        self.farm = farm
        self.integration_type = self.get_integration_type()
    
    @abstractmethod
    def get_integration_type(self) -> str:
        """Return the integration type identifier"""
        pass
    
    @abstractmethod
    def test_connection(self) -> bool:
        """Test if the system is accessible"""
        pass
    
    @abstractmethod
    def sync_house_data(self, farm_id: str) -> Dict[str, Any]:
        """Sync house data from the system"""
        pass
    
    @abstractmethod
    def get_house_count(self, farm_id: str) -> int:
        """Get number of houses from the system"""
        pass
    
    @abstractmethod
    def get_house_age(self, farm_id: str, house_number: int) -> int:
        """Get house age in days from the system"""
        pass
    
    def log_activity(self, action: str, status: str, message: str = "", data_points: int = 0, execution_time: float = None):
        """Log integration activity"""
        IntegrationLog.objects.create(
            farm=self.farm,
            integration_type=self.integration_type,
            action=action,
            status=status,
            message=message,
            data_points_processed=data_points,
            execution_time=execution_time
        )
    
    def log_error(self, error_type: str, error_message: str, error_code: str = "", stack_trace: str = ""):
        """Log integration error"""
        IntegrationError.objects.create(
            farm=self.farm,
            integration_type=self.integration_type,
            error_type=error_type,
            error_message=error_message,
            error_code=error_code,
            stack_trace=stack_trace
        )
    
    def update_health(self, is_healthy: bool, success_rate: float = None, response_time: float = None, last_error: IntegrationError = None):
        """Update integration health metrics"""
        health, created = IntegrationHealth.objects.get_or_create(
            farm=self.farm,
            integration_type=self.integration_type,
            defaults={
                'is_healthy': is_healthy,
                'success_rate_24h': success_rate or 0.0,
                'average_response_time': response_time,
                'last_error': last_error
            }
        )
        
        if not created:
            health.is_healthy = is_healthy
            if success_rate is not None:
                health.success_rate_24h = success_rate
            if response_time is not None:
                health.average_response_time = response_time
            if last_error is not None:
                health.last_error = last_error
            health.save()
    
    def get_health_status(self) -> Optional[IntegrationHealth]:
        """Get current health status"""
        try:
            return IntegrationHealth.objects.get(
                farm=self.farm,
                integration_type=self.integration_type
            )
        except IntegrationHealth.DoesNotExist:
            return None
    
    def is_healthy(self) -> bool:
        """Check if integration is currently healthy"""
        health = self.get_health_status()
        return health.is_healthy if health else False
