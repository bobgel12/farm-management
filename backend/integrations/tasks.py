from celery import shared_task
from django.utils import timezone
from django.db import transaction
from .rotem import RotemIntegration
from .models import IntegrationLog, IntegrationError, IntegrationHealth
from .ml_service import EnhancedMLAnalysisService
from farms.models import Farm
from houses.models import House
import logging

logger = logging.getLogger(__name__)


@shared_task
def sync_farm_data():
    """Sync data for all farms with active integrations"""
    farms = Farm.objects.filter(
        has_system_integration=True,
        integration_status='active'
    )
    
    for farm in farms:
        if farm.integration_type == 'rotem':
            sync_rotem_farm_data.delay(farm.id)
        # Add other integration types here in the future


@shared_task
def sync_rotem_farm_data(farm_id):
    """Sync data for a specific Rotem farm"""
    try:
        farm = Farm.objects.get(id=farm_id)
        integration = RotemIntegration(farm)
        
        # Sync house data
        house_data = integration.sync_house_data(farm.id)
        
        # Update house ages and other data
        if house_data and 'houses' in house_data:
            for house_data_item in house_data['houses']:
                house_number = house_data_item.get('house_number')
                if house_number:
                    try:
                        house = House.objects.get(farm=farm, house_number=house_number)
                        house.current_age_days = house_data_item.get('age_days', house.current_age_days)
                        house.last_system_sync = timezone.now()
                        house.save()
                    except House.DoesNotExist:
                        # Create house if it doesn't exist
                        House.objects.create(
                            farm=farm,
                            house_number=house_number,
                            capacity=1000,
                            is_integrated=True,
                            system_house_id=f'house_{house_number}',
                            current_age_days=house_data_item.get('age_days', 0),
                            chicken_in_date=timezone.now().date(),
                            last_system_sync=timezone.now()
                        )
        
        # Update farm last sync time
        farm.last_sync = timezone.now()
        farm.save()
        
        # Update health status
        integration.update_health(is_healthy=True)
        
    except Farm.DoesNotExist:
        IntegrationError.objects.create(
            farm_id=farm_id,
            integration_type='rotem',
            error_type='farm_not_found',
            error_message=f'Farm with ID {farm_id} not found'
        )
    except Exception as e:
        try:
            farm = Farm.objects.get(id=farm_id)
            IntegrationError.objects.create(
                farm=farm,
                integration_type='rotem',
                error_type='sync_failed',
                error_message=f'Data sync failed: {str(e)}'
            )
            integration = RotemIntegration(farm)
            integration.update_health(is_healthy=False)
        except:
            pass  # If we can't even get the farm, just log the error


@shared_task
def test_integration_connections():
    """Test connections for all integrated farms"""
    farms = Farm.objects.filter(
        has_system_integration=True,
        integration_type__in=['rotem']  # Add other types as needed
    )
    
    for farm in farms:
        if farm.integration_type == 'rotem':
            test_rotem_connection.delay(farm.id)


@shared_task
def test_rotem_connection(farm_id):
    """Test connection for a specific Rotem farm"""
    try:
        farm = Farm.objects.get(id=farm_id)
        integration = RotemIntegration(farm)
        
        success = integration.test_connection()
        
        if success:
            farm.integration_status = 'active'
            farm.save()
            integration.update_health(is_healthy=True)
        else:
            farm.integration_status = 'error'
            farm.save()
            integration.update_health(is_healthy=False)
            
    except Exception as e:
        try:
            farm = Farm.objects.get(id=farm_id)
            farm.integration_status = 'error'
            farm.save()
            IntegrationError.objects.create(
                farm=farm,
                integration_type='rotem',
                error_type='connection_test_failed',
                error_message=f'Connection test failed: {str(e)}'
            )
        except:
            pass


@shared_task
def cleanup_old_integration_logs():
    """Clean up old integration logs (keep last 30 days)"""
    cutoff_date = timezone.now() - timezone.timedelta(days=30)
    
    # Delete old logs
    old_logs = IntegrationLog.objects.filter(timestamp__lt=cutoff_date)
    count = old_logs.count()
    old_logs.delete()
    
    return f"Cleaned up {count} old integration logs"


@shared_task
def update_integration_health_metrics():
    """Update health metrics for all integrations"""
    farms = Farm.objects.filter(has_system_integration=True)
    
    for farm in farms:
        if farm.integration_type == 'rotem':
            try:
                integration = RotemIntegration(farm)
                
                # Calculate success rate for last 24 hours
                yesterday = timezone.now() - timezone.timedelta(hours=24)
                recent_logs = IntegrationLog.objects.filter(
                    farm=farm,
                    integration_type='rotem',
                    timestamp__gte=yesterday
                )
                
                if recent_logs.exists():
                    success_count = recent_logs.filter(status='success').count()
                    total_count = recent_logs.count()
                    success_rate = (success_count / total_count) * 100
                else:
                    success_rate = 0.0
                
                # Update health metrics
                integration.update_health(
                    is_healthy=farm.integration_status == 'active',
                    success_rate=success_rate
                )
                
            except Exception as e:
                IntegrationError.objects.create(
                    farm=farm,
                    integration_type='rotem',
                    error_type='health_update_failed',
                    error_message=f'Health metrics update failed: {str(e)}'
                )


@shared_task
def run_ml_analysis():
    """Run ML analysis for all integrated farms"""
    logger.info("Starting ML analysis task")
    
    try:
        ml_service = EnhancedMLAnalysisService()
        results = ml_service.run_global_analysis()
        
        logger.info(f"ML analysis completed. Generated {len(results)} predictions")
        return f"ML analysis completed. Generated {len(results)} predictions"
        
    except Exception as e:
        logger.error(f"ML analysis task failed: {str(e)}")
        raise


@shared_task
def run_farm_ml_analysis(farm_id):
    """Run ML analysis for a specific farm"""
    logger.info(f"Starting ML analysis for farm {farm_id}")
    
    try:
        ml_service = EnhancedMLAnalysisService()
        results = ml_service.run_farm_analysis(farm_id)
        
        logger.info(f"Farm ML analysis completed for farm {farm_id}. Generated {len(results)} predictions")
        return f"Farm ML analysis completed. Generated {len(results)} predictions"
        
    except Exception as e:
        logger.error(f"Farm ML analysis task failed for farm {farm_id}: {str(e)}")
        raise


@shared_task
def sync_and_analyze_farm(farm_id):
    """Sync data and run ML analysis for a specific farm"""
    logger.info(f"Starting sync and analysis for farm {farm_id}")
    
    try:
        # First sync the data
        if Farm.objects.filter(id=farm_id, integration_type='rotem').exists():
            sync_rotem_farm_data.delay(farm_id)
        
        # Wait a bit for sync to complete, then run analysis
        run_farm_ml_analysis.apply_async(args=[farm_id], countdown=30)
        
        logger.info(f"Sync and analysis initiated for farm {farm_id}")
        return f"Sync and analysis initiated for farm {farm_id}"
        
    except Exception as e:
        logger.error(f"Sync and analysis task failed for farm {farm_id}: {str(e)}")
        raise


@shared_task
def cleanup_old_predictions():
    """Clean up old ML predictions (keep last 30 days)"""
    from rotem_scraper.models import MLPrediction
    
    cutoff_date = timezone.now() - timezone.timedelta(days=30)
    
    # Delete old predictions
    old_predictions = MLPrediction.objects.filter(predicted_at__lt=cutoff_date)
    count = old_predictions.count()
    old_predictions.delete()
    
    logger.info(f"Cleaned up {count} old ML predictions")
    return f"Cleaned up {count} old ML predictions"


@shared_task
def generate_daily_report():
    """Generate daily report for all integrated farms"""
    logger.info("Starting daily report generation")
    
    try:
        farms = Farm.objects.filter(
            has_system_integration=True,
            integration_status='active'
        )
        
        report_data = {
            'date': timezone.now().date().isoformat(),
            'farms_analyzed': farms.count(),
            'total_predictions': 0,
            'anomalies_detected': 0,
            'failure_predictions': 0,
            'optimization_suggestions': 0,
            'farm_summaries': []
        }
        
        for farm in farms:
            try:
                # Get recent predictions for this farm
                from rotem_scraper.models import MLPrediction
                recent_predictions = MLPrediction.objects.filter(
                    controller__farm_id=farm.rotem_farm_id,
                    predicted_at__gte=timezone.now() - timezone.timedelta(days=1)
                )
                
                farm_summary = {
                    'farm_name': farm.name,
                    'integration_type': farm.integration_type,
                    'predictions_count': recent_predictions.count(),
                    'anomalies': recent_predictions.filter(prediction_type='anomaly').count(),
                    'failures': recent_predictions.filter(prediction_type='failure').count(),
                    'optimizations': recent_predictions.filter(prediction_type='optimization').count(),
                    'performance': recent_predictions.filter(prediction_type='performance').count()
                }
                
                report_data['farm_summaries'].append(farm_summary)
                report_data['total_predictions'] += farm_summary['predictions_count']
                report_data['anomalies_detected'] += farm_summary['anomalies']
                report_data['failure_predictions'] += farm_summary['failures']
                report_data['optimization_suggestions'] += farm_summary['optimizations']
                
            except Exception as e:
                logger.error(f"Error generating report for farm {farm.name}: {str(e)}")
                continue
        
        # Log the report
        logger.info(f"Daily report generated: {report_data}")
        
        # In a real implementation, you might save this to a file or send via email
        return report_data
        
    except Exception as e:
        logger.error(f"Daily report generation failed: {str(e)}")
        raise
