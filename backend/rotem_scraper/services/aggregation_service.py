"""
Service for aggregating Rotem data points into daily summaries.
This improves query performance and reduces storage requirements for analytics and ML.
"""
from django.db.models import Avg, Min, Max, Count, Q
from django.utils import timezone
from datetime import date, timedelta
from ..models import RotemDataPoint, RotemDailySummary, RotemController
import logging

logger = logging.getLogger(__name__)


class RotemAggregationService:
    """Service for aggregating Rotem data points into daily summaries"""
    
    # Data type mappings for aggregation
    DATA_TYPE_MAPPINGS = {
        'temperature': {
            'avg_field': 'temperature_avg',
            'min_field': 'temperature_min',
            'max_field': 'temperature_max',
            'count_field': 'temperature_data_points',
        },
        'humidity': {
            'avg_field': 'humidity_avg',
            'min_field': 'humidity_min',
            'max_field': 'humidity_max',
            'count_field': 'humidity_data_points',
        },
        'static_pressure': {
            'avg_field': 'static_pressure_avg',
            'min_field': 'static_pressure_min',
            'max_field': 'static_pressure_max',
            'count_field': 'static_pressure_data_points',
        },
        'wind_speed': {
            'avg_field': 'wind_speed_avg',
            'min_field': 'wind_speed_min',
            'max_field': 'wind_speed_max',
            'count_field': 'wind_speed_data_points',
        },
        'water_consumption': {
            'avg_field': 'water_consumption_avg',
            'min_field': 'water_consumption_min',
            'max_field': 'water_consumption_max',
            'count_field': 'water_consumption_data_points',
        },
        'feed_consumption': {
            'avg_field': 'feed_consumption_avg',
            'min_field': 'feed_consumption_min',
            'max_field': 'feed_consumption_max',
            'count_field': 'feed_consumption_data_points',
        },
    }
    
    @classmethod
    def aggregate_daily_data(cls, controller, target_date=None, force_update=False):
        """
        Aggregate all data points for a controller for a specific date.
        
        Args:
            controller: RotemController instance
            target_date: date object (defaults to yesterday)
            force_update: If True, update existing summary (default: False)
        
        Returns:
            RotemDailySummary instance or None
        """
        if target_date is None:
            target_date = (timezone.now() - timedelta(days=1)).date()
        
        # Check if summary already exists
        summary, created = RotemDailySummary.objects.get_or_create(
            controller=controller,
            date=target_date,
            defaults={}
        )
        
        if not created and not force_update:
            logger.info(f"Daily summary already exists for {controller.controller_name} on {target_date}")
            return summary
        
        # Get all data points for this controller and date
        start_datetime = timezone.make_aware(
            timezone.datetime.combine(target_date, timezone.datetime.min.time())
        )
        end_datetime = start_datetime + timedelta(days=1)
        
        data_points = RotemDataPoint.objects.filter(
            controller=controller,
            timestamp__gte=start_datetime,
            timestamp__lt=end_datetime
        )
        
        if not data_points.exists():
            logger.warning(f"No data points found for {controller.controller_name} on {target_date}")
            if created:
                summary.delete()
            return None
        
        # Initialize summary fields
        summary.total_data_points = data_points.count()
        
        # Aggregate by data type
        for data_type, field_mapping in cls.DATA_TYPE_MAPPINGS.items():
            type_points = data_points.filter(data_type=data_type)
            
            if type_points.exists():
                agg = type_points.aggregate(
                    avg=Avg('value'),
                    min=Min('value'),
                    max=Max('value'),
                    count=Count('id')
                )
                
                setattr(summary, field_mapping['avg_field'], agg['avg'])
                setattr(summary, field_mapping['min_field'], agg['min'])
                setattr(summary, field_mapping['max_field'], agg['max'])
                setattr(summary, field_mapping['count_field'], agg['count'])
        
        # Count quality issues
        summary.anomalies_count = data_points.filter(
            Q(quality='error') | Q(quality='warning')
        ).count()
        summary.warnings_count = data_points.filter(quality='warning').count()
        summary.errors_count = data_points.filter(quality='error').count()
        
        summary.save()
        logger.info(
            f"Created/updated daily summary for {controller.controller_name} on {target_date}: "
            f"{summary.total_data_points} data points"
        )
        
        return summary
    
    @classmethod
    def aggregate_controller_range(cls, controller, start_date, end_date, force_update=False):
        """
        Aggregate data for a controller over a date range.
        
        Args:
            controller: RotemController instance
            start_date: start date (inclusive)
            end_date: end date (inclusive)
            force_update: If True, update existing summaries
        
        Returns:
            List of RotemDailySummary instances
        """
        summaries = []
        current_date = start_date
        
        while current_date <= end_date:
            summary = cls.aggregate_daily_data(controller, current_date, force_update)
            if summary:
                summaries.append(summary)
            current_date += timedelta(days=1)
        
        return summaries
    
    @classmethod
    def aggregate_all_controllers_for_date(cls, target_date=None, force_update=False):
        """
        Aggregate data for all controllers for a specific date.
        
        Args:
            target_date: date object (defaults to yesterday)
            force_update: If True, update existing summaries
        
        Returns:
            Dictionary with results
        """
        if target_date is None:
            target_date = (timezone.now() - timedelta(days=1)).date()
        
        controllers = RotemController.objects.filter(is_connected=True)
        results = {
            'date': target_date,
            'total_controllers': controllers.count(),
            'successful': 0,
            'failed': 0,
            'summaries_created': 0,
            'summaries_updated': 0,
        }
        
        for controller in controllers:
            try:
                summary, created = RotemDailySummary.objects.get_or_create(
                    controller=controller,
                    date=target_date
                )
                
                if not created and not force_update:
                    continue
                
                summary = cls.aggregate_daily_data(controller, target_date, force_update=True)
                
                if summary:
                    results['successful'] += 1
                    if created:
                        results['summaries_created'] += 1
                    else:
                        results['summaries_updated'] += 1
                else:
                    results['failed'] += 1
            except Exception as e:
                logger.error(
                    f"Error aggregating data for {controller.controller_name} on {target_date}: {str(e)}"
                )
                results['failed'] += 1
        
        logger.info(
            f"Aggregation completed for {target_date}: "
            f"{results['successful']} successful, {results['failed']} failed"
        )
        
        return results
    
    @classmethod
    def aggregate_recent_days(cls, days=7, force_update=False):
        """
        Aggregate data for all controllers for the last N days.
        
        Args:
            days: Number of days to aggregate (default: 7)
            force_update: If True, update existing summaries
        
        Returns:
            Dictionary with results
        """
        end_date = (timezone.now() - timedelta(days=1)).date()
        start_date = end_date - timedelta(days=days - 1)
        
        results = {
            'start_date': start_date,
            'end_date': end_date,
            'days_processed': 0,
            'total_summaries': 0,
        }
        
        current_date = start_date
        while current_date <= end_date:
            day_results = cls.aggregate_all_controllers_for_date(current_date, force_update)
            results['days_processed'] += 1
            results['total_summaries'] += day_results['summaries_created'] + day_results['summaries_updated']
            current_date += timedelta(days=1)
        
        return results

