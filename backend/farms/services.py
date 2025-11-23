"""
Services for flock management and operations
"""
from django.db.models import Avg, Sum, Count, Q
from django.utils import timezone
from datetime import timedelta
import uuid
import logging

logger = logging.getLogger(__name__)


class FlockManagementService:
    """Service for flock management operations"""
    
    @staticmethod
    def create_flock_for_house(house, batch_number, breed=None, arrival_date=None, initial_count=0, **kwargs):
        """
        Create a new flock for a house
        
        Args:
            house: House instance
            batch_number: Batch number for the flock
            breed: Breed instance (optional)
            arrival_date: Arrival date (defaults to today)
            initial_count: Initial chicken count
            **kwargs: Additional flock fields
        
        Returns:
            Created Flock instance
        """
        from farms.models import Flock
        
        if not arrival_date:
            arrival_date = timezone.now().date()
        
        # Generate unique flock code
        flock_code = f"{house.farm.name[:3].upper()}-H{house.house_number}-{batch_number}-{uuid.uuid4().hex[:6].upper()}"
        
        flock = Flock.objects.create(
            house=house,
            breed=breed,
            batch_number=batch_number,
            flock_code=flock_code,
            arrival_date=arrival_date,
            initial_chicken_count=initial_count,
            current_chicken_count=initial_count,
            status='arrival',
            is_active=True,
            **kwargs
        )
        
        # Update house status
        house.batch_start_date = arrival_date
        house.current_age_days = 0
        house.save()
        
        logger.info(f"Created flock {flock.flock_code} for house {house}")
        
        return flock
    
    @staticmethod
    def complete_flock(flock, actual_harvest_date=None, final_count=None):
        """
        Complete a flock (harvest)
        
        Args:
            flock: Flock instance
            actual_harvest_date: Actual harvest date (defaults to today)
            final_count: Final chicken count
        
        Returns:
            Updated Flock instance
        """
        if not actual_harvest_date:
            actual_harvest_date = timezone.now().date()
        
        flock.status = 'completed'
        flock.is_active = False
        flock.actual_harvest_date = actual_harvest_date
        flock.end_date = actual_harvest_date
        
        if final_count is not None:
            flock.current_chicken_count = final_count
        
        flock.save()
        
        # Update house status
        flock.house.batch_start_date = None
        flock.house.current_age_days = 0
        flock.house.save()
        
        logger.info(f"Completed flock {flock.flock_code}")
        
        return flock
    
    @staticmethod
    def calculate_flock_performance(flock, record_date=None):
        """
        Calculate and update flock performance metrics
        
        Args:
            flock: Flock instance
            record_date: Date for the performance record
        
        Returns:
            FlockPerformance instance
        """
        from farms.models import FlockPerformance
        
        if not record_date:
            record_date = timezone.now().date()
        
        # Calculate flock age
        flock_age_days = (record_date - flock.arrival_date).days
        
        # Get latest performance record for comparison
        latest_record = flock.performance_records.order_by('-record_date').first()
        
        # Create new performance record
        performance = FlockPerformance.objects.create(
            flock=flock,
            record_date=record_date,
            flock_age_days=flock_age_days,
            current_chicken_count=flock.current_chicken_count or flock.initial_chicken_count
        )
        
        # Calculate derived metrics (these would be populated from actual data)
        if flock.current_chicken_count:
            mortality = flock.initial_chicken_count - flock.current_chicken_count
            performance.mortality_count = mortality
            if flock.initial_chicken_count > 0:
                performance.mortality_rate = (mortality / flock.initial_chicken_count) * 100
                performance.livability = 100 - performance.mortality_rate
        
        performance.save()
        
        logger.info(f"Created performance record for flock {flock.flock_code} on {record_date}")
        
        return performance
    
    @staticmethod
    def get_flock_summary(flock):
        """
        Get comprehensive summary for a flock
        
        Returns:
            dict with flock summary statistics
        """
        performance_records = flock.performance_records.all()
        
        if not performance_records.exists():
            return {
                'flock_id': flock.id,
                'flock_code': flock.flock_code,
                'batch_number': flock.batch_number,
                'arrival_date': flock.arrival_date.isoformat(),
                'current_age_days': flock.current_age_days,
                'initial_count': flock.initial_chicken_count,
                'current_count': flock.current_chicken_count,
                'status': flock.status,
                'has_performance_data': False
            }
        
        latest_record = performance_records.order_by('-record_date').first()
        first_record = performance_records.order_by('record_date').first()
        
        summary = {
            'flock_id': flock.id,
            'flock_code': flock.flock_code,
            'batch_number': flock.batch_number,
            'arrival_date': flock.arrival_date.isoformat(),
            'current_age_days': flock.current_age_days,
            'days_until_harvest': flock.days_until_harvest,
            'initial_count': flock.initial_chicken_count,
            'current_count': flock.current_chicken_count,
            'mortality_count': flock.mortality_count,
            'mortality_rate': flock.mortality_rate,
            'livability': flock.livability,
            'status': flock.status,
            'has_performance_data': True,
            'performance_records_count': performance_records.count(),
            'first_record_date': first_record.record_date.isoformat() if first_record else None,
            'latest_record_date': latest_record.record_date.isoformat() if latest_record else None,
        }
        
        # Add average metrics if available
        if latest_record:
            if latest_record.average_weight_grams:
                summary['latest_average_weight_grams'] = latest_record.average_weight_grams
            
            if latest_record.feed_conversion_ratio:
                summary['latest_fcr'] = latest_record.feed_conversion_ratio
            
            if latest_record.daily_feed_consumption_kg:
                summary['latest_daily_feed_kg'] = latest_record.daily_feed_consumption_kg
        
        return summary
    
    @staticmethod
    def compare_flocks(flocks, metrics=None):
        """
        Compare multiple flocks across specified metrics
        
        Args:
            flocks: QuerySet or list of Flock instances
            metrics: List of metrics to compare (defaults to common metrics)
        
        Returns:
            dict with comparison results
        """
        if metrics is None:
            metrics = ['mortality_rate', 'livability', 'average_weight', 'fcr']
        
        comparison = {
            'flocks': [],
            'metrics': {},
            'summary': {}
        }
        
        for flock in flocks:
            flock_data = {
                'id': flock.id,
                'flock_code': flock.flock_code,
                'batch_number': flock.batch_number,
                'house': str(flock.house),
                'arrival_date': flock.arrival_date.isoformat(),
                'current_age_days': flock.current_age_days,
                'breed': flock.breed.name if flock.breed else None,
            }
            
            # Calculate each metric
            for metric in metrics:
                from analytics.services import KPICalculationService
                value = KPICalculationService.calculate_flock_kpi(flock, metric)
                flock_data[metric] = value
            
            comparison['flocks'].append(flock_data)
        
        # Calculate aggregate statistics for each metric
        for metric in metrics:
            values = [f[metric] for f in comparison['flocks'] if f.get(metric) is not None]
            if values:
                comparison['metrics'][metric] = {
                    'min': min(values),
                    'max': max(values),
                    'average': sum(values) / len(values),
                    'count': len(values)
                }
        
        # Summary statistics
        comparison['summary'] = {
            'total_flocks': len(comparison['flocks']),
            'flocks_with_data': len([f for f in comparison['flocks'] if any(
                f.get(m) is not None for m in metrics
            )])
        }
        
        return comparison

