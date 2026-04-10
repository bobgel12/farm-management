from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from .services.scraper_service import DjangoRotemScraperService
from .services.ml_service import MLAnalysisService
from .models import HouseHeaterRuntimeCache
from houses.models import House
from .scraper import RotemScraper
import logging

logger = logging.getLogger(__name__)


def _derive_record_date(house: House, growth_day: int):
    if growth_day < 0:
        return None
    base_date = house.batch_start_date or house.chicken_in_date
    if not base_date:
        return None
    return base_date + timedelta(days=growth_day)


@shared_task(bind=True, max_retries=3)
def scrape_rotem_data(self, farm_id=None):
    """Celery task to scrape Rotem data for a specific farm or all farms"""
    try:
        logger.info(f"Starting Rotem data scraping task for farm: {farm_id or 'all'}")
        
        # Initialize scraper service
        scraper_service = DjangoRotemScraperService()
        
        if farm_id:
            # Scrape specific farm
            scrape_log = scraper_service.scrape_and_save_data()
            
            if scrape_log.status == 'success':
                logger.info(f"Scraping completed successfully for farm {farm_id}. Collected {scrape_log.data_points_collected} data points")
                
                # Trigger ML analysis
                analyze_data.delay()
                
            else:
                logger.error(f"Scraping failed for farm {farm_id}: {scrape_log.error_message}")
                raise Exception(f"Scraping failed: {scrape_log.error_message}")
        else:
            # Scrape all farms
            results = scraper_service.scrape_all_farms()
            successful_farms = [r for r in results if r['status'] == 'success']
            
            if successful_farms:
                logger.info(f"Scraping completed for {len(successful_farms)} farms")
                
                # Trigger ML analysis
                analyze_data.delay()
            else:
                logger.warning("No farms were successfully scraped")
            
    except Exception as exc:
        logger.error(f"Scraping task failed: {str(exc)}")
        raise self.retry(exc=exc, countdown=60)


@shared_task
def analyze_data():
    """Analyze scraped data with ML models"""
    try:
        logger.info("Starting ML analysis task")
        
        # Initialize ML service
        ml_service = MLAnalysisService()
        
        # Run analysis
        results = ml_service.run_analysis()
        
        logger.info(f"ML analysis completed. Generated {len(results)} predictions")
        
    except Exception as e:
        logger.error(f"ML analysis failed: {str(e)}")
        raise


@shared_task
def train_ml_models():
    """Train ML models with historical data"""
    try:
        logger.info("Starting ML model training task")
        
        # Initialize ML service
        ml_service = MLAnalysisService()
        
        # Train models
        success = ml_service.train_models()
        
        if success:
            logger.info("ML model training completed successfully")
        else:
            logger.warning("ML model training completed with warnings")
        
    except Exception as e:
        logger.error(f"ML model training failed: {str(e)}")
        raise


@shared_task
def cleanup_old_predictions():
    """Clean up old ML predictions to prevent database bloat"""
    try:
        from datetime import timedelta
        from .models import MLPrediction
        
        # Delete predictions older than 30 days
        cutoff_date = timezone.now() - timedelta(days=30)
        deleted_count = MLPrediction.objects.filter(
            predicted_at__lt=cutoff_date
        ).delete()[0]
        
        logger.info(f"Cleaned up {deleted_count} old ML predictions")
        
    except Exception as e:
        logger.error(f"Cleanup task failed: {str(e)}")
        raise


@shared_task(bind=True, max_retries=3)
def collect_monitoring_data(self, farm_id=None):
    """
    Periodic task to collect monitoring data for all integrated farms
    Runs every 5-15 minutes to create monitoring snapshots
    """
    try:
        from farms.models import Farm
        from integrations.rotem import RotemIntegration
        from houses.services.monitoring_service import MonitoringService
        
        logger.info(f"Starting monitoring data collection for farm: {farm_id or 'all'}")
        
        # Get farms with Rotem integration
        if farm_id:
            farms = Farm.objects.filter(
                id=farm_id,
                has_system_integration=True,
                integration_type='rotem',
                is_active=True
            )
        else:
            farms = Farm.objects.filter(
                has_system_integration=True,
                integration_type='rotem',
                is_active=True
            )
        
        total_snapshots = 0
        errors = []
        
        monitoring_service = MonitoringService()
        
        for farm in farms:
            try:
                # Create Rotem integration instance
                integration = RotemIntegration(farm)
                
                # Get sensor data for all houses
                all_house_data = integration.get_all_sensor_data()
                
                if all_house_data:
                    # Create monitoring snapshots
                    snapshots_created = monitoring_service.create_snapshots_for_farm(
                        farm, all_house_data
                    )
                    total_snapshots += snapshots_created
                    
                    logger.info(f"Created {snapshots_created} snapshots for farm {farm.name} (ID: {farm.id})")
                else:
                    logger.warning(f"No house data received for farm {farm.name}")
                    
            except Exception as e:
                error_msg = f"Error collecting data for farm {farm.name} (ID: {farm.id}): {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
        
        result = {
            'status': 'success' if total_snapshots > 0 else 'partial',
            'snapshots_created': total_snapshots,
            'farms_processed': farms.count(),
            'errors': errors,
            'timestamp': timezone.now().isoformat()
        }
        
        logger.info(f"Monitoring collection completed: {total_snapshots} snapshots created")
        return result
        
    except Exception as exc:
        logger.error(f"Monitoring collection task failed: {str(exc)}")
        raise self.retry(exc=exc, countdown=300)  # Retry after 5 minutes


def sync_refresh_house_heater_history(house_id: int) -> dict:
    """
    Fetch CommandID 43 heater history from Rotem and upsert cache.
    Safe to call synchronously from an API view (user-initiated load).
    """
    try:
        house = House.objects.select_related("farm").get(id=house_id)
        farm = house.farm
        if not farm or not farm.rotem_username or not farm.rotem_password:
            return {
                "status": "skipped",
                "reason": "missing_rotem_credentials",
                "house_id": house_id,
            }

        scraper = RotemScraper(farm.rotem_username, farm.rotem_password)
        if not scraper.login():
            return {
                "status": "error",
                "reason": "login_failed",
                "house_id": house_id,
                "error": scraper.last_error_message,
            }

        parsed = scraper.get_heater_history(house_number=house.house_number)
        if not parsed:
            return {
                "status": "error",
                "reason": "empty_response",
                "house_id": house_id,
            }

        source_timestamp = parsed.get("source_timestamp")
        upserted = 0
        all_records = list(parsed.get("records", []))
        summary_row = parsed.get("summary_row")
        if summary_row:
            all_records.append(summary_row)

        for record in all_records:
            growth_day = int(record.get("growth_day", -1))
            _, _ = HouseHeaterRuntimeCache.objects.update_or_create(
                house=house,
                growth_day=growth_day,
                defaults={
                    "record_date": _derive_record_date(house, growth_day),
                    "is_summary_row": bool(record.get("is_summary_row")),
                    "total_runtime_minutes": int(record.get("total_runtime_minutes") or 0),
                    "total_computation_method": record.get("total_computation_method")
                    or "sum_devices",
                    "per_device_json": record.get("per_device") or {},
                    "source_timestamp": source_timestamp,
                    "raw_record_json": record.get("raw_record") or {},
                },
            )
            upserted += 1

        return {
            "status": "success",
            "house_id": house_id,
            "records_upserted": upserted,
            "summary_present": bool(summary_row),
        }
    except House.DoesNotExist:
        return {
            "status": "error",
            "reason": "house_not_found",
            "house_id": house_id,
        }


@shared_task(bind=True, max_retries=2)
def refresh_house_heater_history(self, house_id: int):
    """Celery wrapper for background refresh (optional; on-demand uses sync_refresh)."""
    try:
        return sync_refresh_house_heater_history(house_id)
    except Exception as exc:
        logger.error("refresh_house_heater_history failed: %s", exc, exc_info=True)
        raise self.retry(exc=exc, countdown=30)
