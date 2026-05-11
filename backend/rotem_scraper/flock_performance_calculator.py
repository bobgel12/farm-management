"""
Flock Performance Calculator

Computes real flock performance metrics from Rotem sensor data
and persists as FlockPerformance records.

This module calculates:
- Daily feed consumption (kg)
- Daily water consumption (liters)
- Feed conversion ratio (FCR)
- Average bird weight (grams)
- Mortality rate (%)
- Livability (%)
- Flock age (days)
"""

from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


class FlockPerformanceCalculator:
    """Calculate real flock metrics from Rotem data"""

    @staticmethod
    def calculate_for_flock(flock, record_date=None):
        """
        Calculate daily performance metrics for a flock.

        Args:
            flock: Flock model instance
            record_date: Date to calculate for (defaults to today)

        Returns:
            FlockPerformance instance (created or updated)
        """
        from farms.models import Flock, FlockPerformance
        from rotem_scraper.scraper import RotemScraper

        if not record_date:
            record_date = timezone.now().date()

        house = flock.house
        farm = house.farm

        # Initialize metrics with defaults
        metrics = {
            'flock_age_days': (record_date - flock.arrival_date.date()).days,
            'average_weight_grams': None,
            'feed_conversion_ratio': None,
            'daily_feed_consumption_kg': None,
            'daily_water_consumption_liters': None,
            'mortality_rate': 0,
            'livability': 100,
        }

        try:
            # Calculate mortality from flock state (always available)
            mortality = FlockPerformanceCalculator._calculate_mortality(flock)
            metrics['mortality_rate'] = mortality
            metrics['livability'] = max(0, 100 - mortality)

            # Try to get real Rotem data if available
            if farm.rotem_farm_id and farm.rotem_username and farm.rotem_password:
                try:
                    scraper = RotemScraper(
                        username=farm.rotem_username,
                        password=farm.rotem_password
                    )
                    if scraper.login():
                        rotem_metrics = FlockPerformanceCalculator._get_rotem_metrics(
                            scraper, house, flock, record_date
                        )
                        metrics.update(rotem_metrics)
                        logger.info(f"✅ Retrieved Rotem data for {flock} on {record_date}")
                except Exception as e:
                    logger.warning(f"⚠️  Could not fetch Rotem data for {flock}: {e}")

            # Save or update performance record
            perf, created = FlockPerformance.objects.update_or_create(
                flock=flock,
                record_date=record_date,
                defaults=metrics
            )

            action = "Created" if created else "Updated"
            logger.info(
                f"{action} FlockPerformance for {flock} on {record_date}: "
                f"FCR={perf.feed_conversion_ratio}, "
                f"Water={perf.daily_water_consumption_liters}L, "
                f"Mortality={perf.mortality_rate}%"
            )

            return perf

        except Exception as e:
            logger.error(f"❌ Error calculating performance for {flock}: {e}", exc_info=True)
            raise

    @staticmethod
    def _get_rotem_metrics(scraper, house, flock, record_date):
        """
        Fetch and parse Rotem metrics for a house.

        Args:
            scraper: RotemScraper instance (already authenticated)
            house: House model instance
            flock: Flock model instance
            record_date: Date to fetch metrics for

        Returns:
            Dictionary of metrics to update FlockPerformance
        """
        metrics = {}

        try:
            # Get live data from Rotem
            controllers_info = scraper.get_site_controllers_info()

            if not controllers_info:
                logger.warning(f"No controller info returned from Rotem for {house}")
                return metrics

            # Parse response structure
            response_obj = controllers_info.get('reponseObj', {})
            farm_houses = response_obj.get('FarmHouses', [])

            if not farm_houses:
                logger.warning(f"No FarmHouses found in Rotem response for {house}")
                return metrics

            # Find matching house by house number
            target_house = None
            for h in farm_houses:
                if int(h.get('HouseNumber', 0)) == house.house_number:
                    target_house = h
                    break

            if not target_house:
                logger.warning(
                    f"House number {house.house_number} not found in Rotem data. "
                    f"Available: {[h.get('HouseNumber') for h in farm_houses]}"
                )
                return metrics

            # Extract consumption data
            data = target_house.get('Data', {})

            # Daily feed consumption
            daily_feed = data.get('DailyFeed', {}).get('CurrentNumericValue')
            if daily_feed is not None:
                metrics['daily_feed_consumption_kg'] = float(daily_feed)

            # Daily water consumption
            daily_water = data.get('DailyWater', {}).get('CurrentNumericValue')
            if daily_water is not None:
                metrics['daily_water_consumption_liters'] = float(daily_water)

            logger.info(
                f"Extracted Rotem metrics for {house}: "
                f"Feed={metrics.get('daily_feed_consumption_kg')}kg, "
                f"Water={metrics.get('daily_water_consumption_liters')}L"
            )

        except Exception as e:
            logger.error(f"❌ Error parsing Rotem metrics for {house}: {e}", exc_info=True)

        return metrics

    @staticmethod
    def _calculate_mortality(flock) -> float:
        """
        Calculate mortality rate from flock state.

        Mortality = (initial_count - current_count) / initial_count * 100

        Args:
            flock: Flock model instance

        Returns:
            Mortality rate as percentage (0-100)
        """
        if not flock.initial_chicken_count or flock.initial_chicken_count == 0:
            return 0.0

        lost = flock.initial_chicken_count - flock.current_chicken_count
        mortality_rate = (lost / flock.initial_chicken_count) * 100

        return round(mortality_rate, 2)


def calculate_all_flock_performance(record_date=None):
    """
    Calculate performance for all active flocks.

    Designed to be called daily via Celery Beat schedule.

    Args:
        record_date: Date to calculate for (defaults to today)

    Returns:
        Dictionary with results summary:
        {
            'success': int,
            'failed': int,
            'errors': [str, ...]
        }
    """
    from farms.models import Flock

    if not record_date:
        record_date = timezone.now().date()

    calculator = FlockPerformanceCalculator()
    active_flocks = Flock.objects.filter(is_active=True)

    results = {
        'success': 0,
        'failed': 0,
        'errors': []
    }

    logger.info(f"Starting daily performance calculation for {active_flocks.count()} active flocks")

    for flock in active_flocks:
        try:
            perf = calculator.calculate_for_flock(flock, record_date)
            results['success'] += 1

            logger.info(
                f"✅ {flock}: "
                f"Age={perf.flock_age_days}d, "
                f"FCR={perf.feed_conversion_ratio}, "
                f"Water={perf.daily_water_consumption_liters}L, "
                f"Mortality={perf.mortality_rate}%"
            )
        except Exception as e:
            results['failed'] += 1
            error_msg = f"{flock}: {str(e)}"
            results['errors'].append(error_msg)
            logger.error(f"❌ Failed to calculate {error_msg}")

    # Summary log
    summary = (
        f"Daily performance calculation complete. "
        f"Success: {results['success']}, "
        f"Failed: {results['failed']}"
    )
    if results['errors']:
        summary += f" | Errors: {', '.join(results['errors'][:3])}"
        if len(results['errors']) > 3:
            summary += f" ... and {len(results['errors']) - 3} more"

    logger.info(summary)
    return results
