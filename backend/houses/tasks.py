"""
Celery tasks for house monitoring and alerts
"""
from celery import shared_task
from django.utils import timezone
from django.db.models import Q
from houses.models import House, WaterConsumptionAlert
from houses.services.water_anomaly_detector import WaterAnomalyDetector
from houses.services.water_alert_email_service import WaterAlertEmailService
from farms.models import Farm
import logging

logger = logging.getLogger(__name__)


def monitor_water_consumption_impl(house_id=None, farm_id=None):
    """
    Internal implementation of water consumption monitoring
    Can be called directly (synchronously) or via Celery task
    
    Args:
        house_id: Optional specific house ID to monitor
        farm_id: Optional specific farm ID to monitor all houses in that farm
    
    Returns:
        Dict with summary of monitoring results
    """
    logger.info(f"Starting water consumption monitoring (house_id={house_id}, farm_id={farm_id})")
    
    # Get houses to monitor - filter by actual database fields (not the property)
    # is_integrated is a property that checks has_system_integration and integration_status == 'active'
    houses_query = House.objects.filter(
        farm__has_system_integration=True,
        farm__integration_status='active',
        farm__integration_type='rotem'
    )
    
    if house_id:
        houses_query = houses_query.filter(pk=house_id)
    elif farm_id:
        houses_query = houses_query.filter(farm_id=farm_id)
    
    houses = houses_query.select_related('farm').all()
    
    if not houses.exists():
        logger.info("No Rotem-integrated houses found to monitor")
        return {
            'status': 'success',
            'houses_checked': 0,
            'alerts_created': 0,
            'emails_sent': 0
        }
    
    logger.info(f"Monitoring {houses.count()} houses for water consumption anomalies")
    
    total_alerts = 0
    total_emails = 0
    
    for house in houses:
        try:
            # Detect anomalies
            detector = WaterAnomalyDetector(house)
            anomalies = detector.detect_anomalies(days_to_check=1)  # Check today's data
            
            for anomaly_data in anomalies:
                # Create alert record
                alert, created = WaterConsumptionAlert.objects.get_or_create(
                    house=house,
                    farm=house.farm,
                    alert_date=anomaly_data['alert_date'],
                    defaults={
                        'growth_day': anomaly_data.get('growth_day'),
                        'current_consumption': anomaly_data['current_consumption'],
                        'baseline_consumption': anomaly_data['baseline_consumption'],
                        'expected_consumption': anomaly_data.get('expected_consumption'),
                        'increase_percentage': anomaly_data['increase_percentage'],
                        'severity': anomaly_data['severity'],
                        'message': anomaly_data['message'],
                        'detection_method': anomaly_data['detection_method'],
                    }
                )
                
                if created:
                    total_alerts += 1
                    logger.info(f"Created water consumption alert {alert.id} for House {house.house_number}")
                    
                    # Send email alert
                    email_sent = WaterAlertEmailService.send_alert_email(alert)
                    if email_sent:
                        total_emails += 1
                        logger.info(f"Sent email alert for water consumption alert {alert.id}")
                    else:
                        logger.warning(f"Failed to send email for water consumption alert {alert.id}")
                else:
                    logger.debug(f"Alert already exists for House {house.house_number} on {anomaly_data['alert_date']}")
        
        except Exception as e:
            logger.error(f"Error monitoring water consumption for house {house.id}: {str(e)}", exc_info=True)
            # Continue with next house even if one fails
            continue
    
    result = {
        'status': 'success',
        'houses_checked': houses.count(),
        'alerts_created': total_alerts,
        'emails_sent': total_emails,
        'timestamp': timezone.now().isoformat()
    }
    
    logger.info(f"Water consumption monitoring completed: {result}")
    return result


@shared_task(bind=True, max_retries=3)
def monitor_water_consumption(self, house_id=None, farm_id=None):
    """
    Monitor water consumption for houses and detect anomalies (Celery task)
    
    This function can be called:
    - As a Celery task (asynchronously): monitor_water_consumption.delay(...)
    - The implementation can be called directly: monitor_water_consumption_impl(...)
    
    Args:
        house_id: Optional specific house ID to monitor
        farm_id: Optional specific farm ID to monitor all houses in that farm
    
    Returns:
        Dict with summary of monitoring results
    """
    try:
        return monitor_water_consumption_impl(house_id=house_id, farm_id=farm_id)
    except Exception as exc:
        logger.error(f"Water consumption monitoring task failed: {str(exc)}", exc_info=True)
        raise self.retry(exc=exc, countdown=300)  # Retry after 5 minutes


@shared_task
def cleanup_old_water_alerts():
    """
    Cleanup old acknowledged water consumption alerts (older than 90 days)
    """
    try:
        from datetime import timedelta
        cutoff_date = timezone.now() - timedelta(days=90)
        
        old_alerts = WaterConsumptionAlert.objects.filter(
            is_acknowledged=True,
            created_at__lt=cutoff_date
        )
        
        count = old_alerts.count()
        old_alerts.delete()
        
        logger.info(f"Cleaned up {count} old water consumption alerts")
        return {'status': 'success', 'deleted_count': count}
    
    except Exception as e:
        logger.error(f"Error cleaning up old water alerts: {str(e)}", exc_info=True)
        return {'status': 'error', 'error': str(e)}

