from celery import shared_task
from django.utils import timezone
from .services.scraper_service import DjangoRotemScraperService
from .services.ml_service import MLAnalysisService
import logging

logger = logging.getLogger(__name__)


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
