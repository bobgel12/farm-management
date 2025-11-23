"""
Services for analytics and KPI calculations
"""
from django.db.models import Avg, Sum, Count, Q, F, FloatField
from django.db.models.functions import TruncDate, TruncWeek, TruncMonth
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


class KPICalculationService:
    """Service for calculating KPIs"""
    
    @staticmethod
    def calculate_flock_kpi(flock, metric_type, period_start=None, period_end=None):
        """
        Calculate KPI for a single flock
        
        Args:
            flock: Flock instance
            metric_type: Type of metric (fcr, mortality_rate, weight_gain, etc.)
            period_start: Start date for calculation period
            period_end: End date for calculation period
        
        Returns:
            Calculated value or None
        """
        try:
            # Get performance records
            performance_records = flock.performance_records.all()
            
            if period_start:
                performance_records = performance_records.filter(record_date__gte=period_start)
            if period_end:
                performance_records = performance_records.filter(record_date__lte=period_end)
            
            performance_records = performance_records.order_by('record_date')
            
            if not performance_records.exists():
                return None
            
            # Calculate based on metric type
            if metric_type == 'mortality_rate':
                return flock.mortality_rate
            
            elif metric_type == 'livability':
                return flock.livability
            
            elif metric_type == 'fcr' or metric_type == 'feed_conversion_ratio':
                return KPICalculationService._calculate_fcr(performance_records, flock)
            
            elif metric_type == 'average_weight':
                weights = [r.average_weight_grams for r in performance_records if r.average_weight_grams]
                if weights:
                    return sum(weights) / len(weights)
                return None
            
            elif metric_type == 'weight_gain':
                return KPICalculationService._calculate_weight_gain(performance_records)
            
            elif metric_type == 'feed_consumption':
                total_feed = performance_records.aggregate(
                    total=Sum('feed_consumed_kg')
                )['total']
                return total_feed if total_feed else None
            
            elif metric_type == 'water_consumption':
                total_water = performance_records.aggregate(
                    total=Sum('daily_water_consumption_liters')
                )['total']
                return total_water if total_water else None
            
            return None
            
        except Exception as e:
            logger.error(f"Error calculating KPI for flock {flock.id}: {str(e)}")
            return None
    
    @staticmethod
    def _calculate_fcr(performance_records, flock):
        """Calculate Feed Conversion Ratio"""
        if not performance_records.exists():
            return None
        
        # Get total feed consumed
        last_record = performance_records.last()
        total_feed = last_record.feed_consumed_kg if last_record and last_record.feed_consumed_kg else None
        
        if not total_feed or total_feed == 0:
            return None
        
        # Calculate weight gain
        first_record = performance_records.first()
        if not first_record or not first_record.average_weight_grams:
            return None
        
        initial_weight_kg = (first_record.average_weight_grams * flock.initial_chicken_count) / 1000
        current_weight_kg = last_record.total_weight_kg if last_record and last_record.total_weight_kg else None
        
        if not current_weight_kg or initial_weight_kg == 0:
            return None
        
        weight_gain_kg = current_weight_kg - initial_weight_kg
        
        if weight_gain_kg <= 0:
            return None
        
        # FCR = Feed consumed / Weight gain
        fcr = total_feed / weight_gain_kg
        return round(fcr, 3)
    
    @staticmethod
    def _calculate_weight_gain(performance_records):
        """Calculate weight gain from performance records"""
        if not performance_records.exists():
            return None
        
        first_record = performance_records.first()
        last_record = performance_records.last()
        
        if not first_record or not last_record:
            return None
        
        if not first_record.average_weight_grams or not last_record.average_weight_grams:
            return None
        
        weight_gain = last_record.average_weight_grams - first_record.average_weight_grams
        return round(weight_gain, 2)
    
    @staticmethod
    def calculate_organization_kpi(organization, kpi_config, calculation_date=None, filters=None):
        """
        Calculate KPI for an organization
        
        Args:
            organization: Organization instance
            kpi_config: KPI configuration dict
            calculation_date: Date for calculation (defaults to today)
            filters: Additional filters dict
        
        Returns:
            Calculated KPI value
        """
        if not calculation_date:
            calculation_date = timezone.now().date()
        
        metric_type = kpi_config.get('metric_type')
        calculation_config = kpi_config.get('calculation_config', {})
        data_source = calculation_config.get('data_source', 'flocks')
        
        try:
            if data_source == 'flocks':
                return KPICalculationService._calculate_flock_aggregate_kpi(
                    organization, metric_type, calculation_date, filters
                )
            
            elif data_source == 'farms':
                return KPICalculationService._calculate_farm_kpi(
                    organization, metric_type, calculation_date, filters
                )
            
            elif data_source == 'houses':
                return KPICalculationService._calculate_house_kpi(
                    organization, metric_type, calculation_date, filters
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error calculating organization KPI: {str(e)}")
            return None
    
    @staticmethod
    def _calculate_flock_aggregate_kpi(organization, metric_type, calculation_date, filters):
        """Calculate aggregate KPI across all flocks in organization"""
        from farms.models import Flock
        
        flocks = Flock.objects.filter(
            house__farm__organization=organization,
            is_active=True
        )
        
        # Apply filters
        if filters:
            if 'farm_id' in filters:
                flocks = flocks.filter(house__farm_id=filters['farm_id'])
            if 'breed_id' in filters:
                flocks = flocks.filter(breed_id=filters['breed_id'])
            if 'status' in filters:
                flocks = flocks.filter(status=filters['status'])
        
        values = []
        for flock in flocks:
            value = KPICalculationService.calculate_flock_kpi(flock, metric_type)
            if value is not None:
                values.append(value)
        
        if not values:
            return None
        
        # Calculate aggregate based on metric type
        if metric_type in ['fcr', 'feed_conversion_ratio', 'mortality_rate', 'livability', 'average_weight']:
            return round(sum(values) / len(values), 3)
        elif metric_type in ['feed_consumption', 'water_consumption', 'weight_gain']:
            return round(sum(values), 2)
        else:
            return round(sum(values) / len(values), 3)
    
    @staticmethod
    def _calculate_farm_kpi(organization, metric_type, calculation_date, filters):
        """Calculate KPI across farms"""
        from farms.models import Farm
        
        farms = Farm.objects.filter(
            organization=organization,
            is_active=True
        )
        
        # This would aggregate farm-level metrics
        # Implementation depends on specific metrics needed
        return None
    
    @staticmethod
    def _calculate_house_kpi(organization, metric_type, calculation_date, filters):
        """Calculate KPI across houses"""
        from houses.models import House
        
        houses = House.objects.filter(
            farm__organization=organization,
            is_active=True
        )
        
        # This would aggregate house-level metrics
        # Implementation depends on specific metrics needed
        return None


class TrendAnalysisService:
    """Service for trend analysis"""
    
    @staticmethod
    def analyze_flock_trend(flock, metric_type, period_days=30):
        """
        Analyze trend for a flock metric over time
        
        Returns:
            dict with trend data (values, dates, trend direction, change_percentage)
        """
        from farms.models import FlockPerformance
        
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=period_days)
        
        records = FlockPerformance.objects.filter(
            flock=flock,
            record_date__gte=start_date,
            record_date__lte=end_date
        ).order_by('record_date')
        
        if not records.exists():
            return None
        
        # Extract values based on metric type
        values = []
        dates = []
        
        for record in records:
            dates.append(record.record_date.isoformat())
            
            if metric_type == 'weight':
                values.append(record.average_weight_grams)
            elif metric_type == 'mortality_rate':
                values.append(record.mortality_rate)
            elif metric_type == 'feed_consumption':
                values.append(record.daily_feed_consumption_kg)
            elif metric_type == 'fcr':
                values.append(record.feed_conversion_ratio)
            else:
                values.append(None)
        
        # Calculate trend
        if len(values) >= 2:
            first_half_avg = sum(values[:len(values)//2]) / (len(values)//2)
            second_half_avg = sum(values[len(values)//2:]) / (len(values) - len(values)//2)
            
            change = second_half_avg - first_half_avg
            change_percentage = (change / first_half_avg * 100) if first_half_avg > 0 else 0
            
            trend_direction = 'increasing' if change > 0 else 'decreasing' if change < 0 else 'stable'
        else:
            trend_direction = 'stable'
            change_percentage = 0
        
        return {
            'values': values,
            'dates': dates,
            'trend_direction': trend_direction,
            'change_percentage': round(change_percentage, 2),
            'period_days': period_days
        }
    
    @staticmethod
    def compare_flocks_trend(flocks, metric_type, period_days=30):
        """Compare trends across multiple flocks"""
        trends = []
        
        for flock in flocks:
            trend = TrendAnalysisService.analyze_flock_trend(flock, metric_type, period_days)
            if trend:
                trend['flock_id'] = flock.id
                trend['flock_name'] = str(flock)
                trends.append(trend)
        
        return trends


class BenchmarkingService:
    """Service for benchmarking and comparison"""
    
    @staticmethod
    def compare_flock_to_benchmark(flock, benchmark):
        """
        Compare a flock's performance to a benchmark
        
        Returns:
            dict with comparison results
        """
        from analytics.models import Benchmark
        
        metric_name = benchmark.metric_name
        
        # Map metric names to KPI calculation methods
        metric_type_map = {
            'FCR': 'fcr',
            'Feed Conversion Ratio': 'fcr',
            'Mortality Rate': 'mortality_rate',
            'Livability': 'livability',
            'Average Weight': 'average_weight',
            'Weight Gain': 'weight_gain'
        }
        
        metric_type = metric_type_map.get(metric_name, metric_name.lower())
        
        # Calculate flock's current value
        flock_value = KPICalculationService.calculate_flock_kpi(flock, metric_type)
        
        if flock_value is None:
            return None
        
        benchmark_avg = benchmark.average_value
        
        # Calculate deviation
        deviation = flock_value - benchmark_avg
        deviation_percentage = (deviation / benchmark_avg * 100) if benchmark_avg > 0 else 0
        
        # Determine performance category
        if deviation_percentage > 10:
            performance_category = 'below_expectation'
        elif deviation_percentage < -10:
            performance_category = 'above_expectation'
        else:
            performance_category = 'within_expectation'
        
        return {
            'flock_id': flock.id,
            'flock_name': str(flock),
            'metric_name': metric_name,
            'flock_value': flock_value,
            'benchmark_average': benchmark_avg,
            'benchmark_min': benchmark.min_value,
            'benchmark_max': benchmark.max_value,
            'deviation': round(deviation, 3),
            'deviation_percentage': round(deviation_percentage, 2),
            'performance_category': performance_category,
            'unit': benchmark.unit
        }
    
    @staticmethod
    def get_organization_benchmarks(organization, metric_name=None):
        """Get relevant benchmarks for an organization"""
        from analytics.models import Benchmark
        
        benchmarks = Benchmark.objects.filter(
            organization=organization,
            is_active=True
        )
        
        if metric_name:
            benchmarks = benchmarks.filter(metric_name__icontains=metric_name)
        
        return benchmarks


class CorrelationAnalysisService:
    """Service for correlation analysis between metrics"""
    
    @staticmethod
    def analyze_correlation(flock, metric1, metric2, period_days=30):
        """
        Analyze correlation between two metrics for a flock
        
        Returns:
            dict with correlation coefficient and analysis
        """
        from farms.models import FlockPerformance
        
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=period_days)
        
        records = FlockPerformance.objects.filter(
            flock=flock,
            record_date__gte=start_date,
            record_date__lte=end_date
        ).order_by('record_date')
        
        if not records.exists():
            return None
        
        # Extract values for both metrics
        values1 = []
        values2 = []
        
        for record in records:
            val1 = CorrelationAnalysisService._get_metric_value(record, metric1)
            val2 = CorrelationAnalysisService._get_metric_value(record, metric2)
            
            if val1 is not None and val2 is not None:
                values1.append(val1)
                values2.append(val2)
        
        if len(values1) < 3:
            return None
        
        # Calculate correlation coefficient (Pearson correlation)
        correlation = CorrelationAnalysisService._calculate_pearson_correlation(values1, values2)
        
        # Determine correlation strength
        abs_correlation = abs(correlation)
        if abs_correlation > 0.7:
            strength = 'strong'
        elif abs_correlation > 0.4:
            strength = 'moderate'
        elif abs_correlation > 0.2:
            strength = 'weak'
        else:
            strength = 'negligible'
        
        return {
            'metric1': metric1,
            'metric2': metric2,
            'correlation_coefficient': round(correlation, 3),
            'strength': strength,
            'period_days': period_days,
            'data_points': len(values1)
        }
    
    @staticmethod
    def _get_metric_value(record, metric_name):
        """Get metric value from a performance record"""
        metric_map = {
            'weight': record.average_weight_grams,
            'temperature': record.average_temperature,
            'humidity': record.average_humidity,
            'feed_consumption': record.daily_feed_consumption_kg,
            'water_consumption': record.daily_water_consumption_liters,
            'fcr': record.feed_conversion_ratio,
            'mortality_rate': record.mortality_rate,
            'livability': record.livability
        }
        
        return metric_map.get(metric_name.lower())
    
    @staticmethod
    def _calculate_pearson_correlation(x, y):
        """Calculate Pearson correlation coefficient"""
        n = len(x)
        
        if n == 0:
            return 0
        
        # Calculate means
        mean_x = sum(x) / n
        mean_y = sum(y) / n
        
        # Calculate covariance and variances
        covariance = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
        variance_x = sum((x[i] - mean_x) ** 2 for i in range(n))
        variance_y = sum((y[i] - mean_y) ** 2 for i in range(n))
        
        # Calculate correlation
        denominator = (variance_x * variance_y) ** 0.5
        
        if denominator == 0:
            return 0
        
        correlation = covariance / denominator
        return correlation

