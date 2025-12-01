"""
Water consumption anomaly detection service
Detects abnormal increases in water consumption using statistical methods
"""
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta, date
from django.utils import timezone
from django.db.models import Avg, StdDev, Q
from houses.models import House, WaterConsumptionAlert
from rotem_scraper.services.scraper_service import DjangoRotemScraperService
from rotem_scraper.scraper import RotemScraper
import statistics

logger = logging.getLogger(__name__)


class WaterAnomalyDetector:
    """Service to detect abnormal water consumption patterns"""
    
    # Thresholds for anomaly detection (now based on deviation from expected age-adjusted consumption)
    LOW_THRESHOLD = 1.3  # 30% above expected for age
    MEDIUM_THRESHOLD = 1.5  # 50% above expected
    HIGH_THRESHOLD = 2.0  # 100% above expected (double)
    CRITICAL_THRESHOLD = 2.5  # 150% above expected
    
    # Minimum number of historical data points required
    MIN_HISTORICAL_DAYS = 3  # Reduced since we're using age-adjusted baselines
    
    # Expected water consumption per bird per day by age (in liters)
    # Based on research: broiler chickens consume 0.05-0.77 L/bird/day depending on age
    # These are baseline values at 21°C, adjusted for temperature
    EXPECTED_WATER_CONSUMPTION_BY_AGE = {
        # Days 1-7: 0.05-0.10 L/bird/day
        (1, 7): 0.075,
        # Days 8-14: 0.10-0.15 L/bird/day
        (8, 14): 0.125,
        # Days 15-21: 0.15-0.20 L/bird/day
        (15, 21): 0.175,
        # Days 22-28: 0.20-0.30 L/bird/day
        (22, 28): 0.25,
        # Days 29-35: 0.30-0.40 L/bird/day
        (29, 35): 0.35,
        # Days 36-42: 0.40-0.55 L/bird/day
        (36, 42): 0.475,
        # Days 43-49: 0.55-0.70 L/bird/day
        (43, 49): 0.625,
        # Days 50+: 0.70-0.77 L/bird/day
        (50, 100): 0.735,
    }
    
    # Temperature adjustment factor: 25% increase per 5°C above 20°C
    TEMP_BASE = 20.0  # Base temperature in Celsius
    TEMP_ADJUSTMENT_PER_5C = 0.25  # 25% increase per 5°C
    
    def __init__(self, house: House):
        self.house = house
        self.farm = house.farm
    
    def detect_anomalies(self, days_to_check: int = 1) -> List[Dict]:
        """
        Detect water consumption anomalies for the house
        
        Args:
            days_to_check: Number of recent days to check for anomalies (default: 1, checks today)
        
        Returns:
            List of detected anomalies, each containing:
            - alert_date: Date of the anomaly
            - current_consumption: Current water consumption
            - baseline_consumption: Baseline/average consumption
            - increase_percentage: Percentage increase
            - severity: Alert severity level
            - message: Alert message
        """
        if not self.farm or not self.farm.is_integrated:
            logger.warning(f"House {self.house.house_number} is not connected to a Rotem-integrated farm")
            return []
        
        anomalies = []
        
        try:
            # Fetch water history from Rotem API
            scraper_service = DjangoRotemScraperService(farm_id=self.farm.rotem_farm_id)
            scraper = RotemScraper(
                scraper_service.credentials['username'],
                scraper_service.credentials['password']
            )
            
            # Login to Rotem
            logger.info(f"Logging in to Rotem for farm {self.farm.rotem_farm_id}...")
            if not scraper.login():
                logger.error(f"Failed to log in to Rotem for farm {self.farm.rotem_farm_id}")
                return []
            
            # Get water history (last 30 days for baseline calculation)
            # NOTE: Currently using daily aggregated data (CommandID 40)
            # For better accuracy, we could use hourly data (CommandID 48) which provides
            # more granular data points, but daily data is sufficient for anomaly detection
            # as we're comparing daily consumption patterns against age-adjusted baselines
            raw_water_data = scraper.get_water_history(
                house_number=self.house.house_number,
                start_date=None,
                end_date=None
            )
            
            if not raw_water_data or not raw_water_data.get('isSucceed'):
                logger.warning(f"No water history data available for house {self.house.house_number}")
                return []
            
            # Parse water history from Rotem API response
            water_history = self._parse_water_history(raw_water_data)
            
            if len(water_history) < self.MIN_HISTORICAL_DAYS:
                logger.info(f"Insufficient historical data for house {self.house.house_number} "
                          f"({len(water_history)} days, need {self.MIN_HISTORICAL_DAYS})")
                return []
            
            # Get current bird count and temperature for age-adjusted baseline calculation
            from houses.models import HouseMonitoringSnapshot
            latest_snapshot = HouseMonitoringSnapshot.objects.filter(
                house=self.house
            ).order_by('-timestamp').first()
            
            bird_count = latest_snapshot.bird_count if latest_snapshot and latest_snapshot.bird_count else None
            if not bird_count:
                # Try to get from house or flock
                from farms.models import Flock
                active_flock = Flock.objects.filter(house=self.house, is_active=True).first()
                if active_flock:
                    bird_count = active_flock.current_chicken_count
            
            current_temp = latest_snapshot.average_temperature if latest_snapshot and latest_snapshot.average_temperature else None
            
            # Check recent days for anomalies
            recent_days = water_history[-days_to_check:] if days_to_check > 0 else []
            
            for day_data in recent_days:
                current_consumption = day_data['consumption']
                alert_date = day_data['date']
                growth_day = day_data.get('growth_day')
                
                # Skip if we already have an alert for this date
                if WaterConsumptionAlert.objects.filter(
                    house=self.house,
                    alert_date=alert_date
                ).exists():
                    continue
                
                # Calculate age-adjusted expected consumption
                expected_consumption = self._calculate_expected_consumption(
                    growth_day=growth_day,
                    bird_count=bird_count,
                    temperature=current_temp
                )
                
                # Also calculate historical baseline for comparison (using similar age days)
                # Find historical days with similar growth days (±3 days)
                similar_age_data = []
                for hist_day in water_history:
                    hist_growth_day = hist_day.get('growth_day')
                    if hist_growth_day and growth_day:
                        if abs(hist_growth_day - growth_day) <= 3 and hist_day['date'] < alert_date:
                            similar_age_data.append(hist_day['consumption'])
                
                # Use age-adjusted expected as primary baseline
                if expected_consumption and expected_consumption > 0:
                    baseline_consumption = expected_consumption
                    # Calculate standard deviation from similar age days if available
                    if similar_age_data and len(similar_age_data) > 1:
                        baseline_std = statistics.stdev(similar_age_data)
                        # Use average of similar age days as secondary baseline
                        historical_baseline = statistics.mean(similar_age_data)
                        # Use the higher of expected or historical (to avoid false positives)
                        baseline_consumption = max(expected_consumption, historical_baseline * 0.9)
                    else:
                        # Use 20% variance for expected consumption if no historical data
                        baseline_std = expected_consumption * 0.2
                elif similar_age_data:
                    # Fallback to historical similar age data
                    baseline_consumption = statistics.mean(similar_age_data)
                    baseline_std = statistics.stdev(similar_age_data) if len(similar_age_data) > 1 else baseline_consumption * 0.2
                else:
                    # Last resort: use all historical data
                    baseline_data = water_history[:-days_to_check] if days_to_check > 0 else water_history
                    baseline_consumption = statistics.mean([d['consumption'] for d in baseline_data])
                    baseline_std = statistics.stdev([d['consumption'] for d in baseline_data]) if len(baseline_data) > 1 else baseline_consumption * 0.2
                
                # Calculate increase percentage and ratio
                if baseline_consumption > 0:
                    increase_percentage = ((current_consumption - baseline_consumption) / baseline_consumption) * 100
                    increase_ratio = current_consumption / baseline_consumption
                else:
                    increase_percentage = 0
                    increase_ratio = 0
                
                # Determine severity based on increase ratio (now against age-adjusted baseline)
                severity = self._determine_severity(increase_ratio, baseline_std, current_consumption, expected_consumption)
                
                # Only create alert if severity is at least 'low'
                if severity:
                    anomaly = {
                        'alert_date': alert_date,
                        'growth_day': growth_day,
                        'current_consumption': current_consumption,
                        'baseline_consumption': baseline_consumption,
                        'expected_consumption': expected_consumption,  # Age-adjusted expected
                        'increase_percentage': increase_percentage,
                        'increase_ratio': increase_ratio,
                        'severity': severity,
                        'message': self._generate_alert_message(
                            current_consumption,
                            baseline_consumption,
                            expected_consumption,
                            increase_percentage,
                            severity,
                            alert_date,
                            growth_day
                        ),
                        'detection_method': 'age_adjusted_statistical'
                    }
                    anomalies.append(anomaly)
                    logger.info(f"Anomaly detected for House {self.house.house_number} on {alert_date} (Day {growth_day}): "
                              f"{current_consumption:.2f}L/day vs expected {expected_consumption:.2f}L/day "
                              f"({increase_percentage:.1f}% above baseline)")
        
        except Exception as e:
            logger.error(f"Error detecting water consumption anomalies for house {self.house.house_number}: {str(e)}", exc_info=True)
        
        return anomalies
    
    def _parse_water_history(self, raw_water_data: Dict) -> List[Dict]:
        """
        Parse water history from Rotem API response
        
        Returns list of dicts with:
        - date: Date object
        - consumption: Water consumption in L/day
        - growth_day: Growth day number (optional)
        """
        water_history = []
        response_obj = raw_water_data.get('reponseObj', {})
        
        # Check dsData.Data array (CommandID 40 format)
        if 'dsData' in response_obj:
            ds_data = response_obj['dsData']
            if 'Data' in ds_data and isinstance(ds_data['Data'], list):
                for record in ds_data['Data']:
                    if isinstance(record, dict):
                        growth_day_str = record.get('HistoryViewItem_GROWTH_DAY') or record.get('HistoryRecord_GrowthDay')
                        growth_day = int(float(growth_day_str)) if growth_day_str else None
                        
                        if growth_day is None or growth_day < 0:
                            continue
                        
                        # Extract total water consumption
                        water_con_str = record.get('HistoryViewItem_WATER_CON') or record.get('HistoryRecord_TotalDrink') or record.get('HistoryRecord_TotalWater')
                        consumption_value = float(str(water_con_str).replace(',', '')) if water_con_str else 0
                        
                        if consumption_value > 0:
                            # Calculate actual date from growth day
                            actual_date = None
                            if self.house.batch_start_date:
                                actual_date = self.house.batch_start_date + timedelta(days=growth_day)
                            elif self.house.chicken_in_date:
                                actual_date = self.house.chicken_in_date + timedelta(days=growth_day)
                            else:
                                # Fallback: use current date minus days
                                actual_date = timezone.now().date() - timedelta(days=(30 - growth_day))
                            
                            water_history.append({
                                'date': actual_date,
                                'consumption': consumption_value,
                                'growth_day': growth_day,
                            })
        
        # Sort by date
        water_history.sort(key=lambda x: x['date'])
        
        return water_history
    
    def _calculate_expected_consumption(self, growth_day: Optional[int], bird_count: Optional[int], temperature: Optional[float]) -> Optional[float]:
        """
        Calculate expected water consumption based on growth day, bird count, and temperature
        
        Args:
            growth_day: Current growth day (age of chickens)
            bird_count: Number of birds in the house
            temperature: Current average temperature in Celsius
        
        Returns:
            Expected water consumption in L/day, or None if insufficient data
        """
        if not growth_day or growth_day < 1:
            return None
        
        # Get expected consumption per bird per day based on age
        expected_per_bird = None
        for (min_age, max_age), consumption in self.EXPECTED_WATER_CONSUMPTION_BY_AGE.items():
            if min_age <= growth_day <= max_age:
                expected_per_bird = consumption
                break
        
        # If growth day is beyond our range, use the maximum
        if expected_per_bird is None:
            expected_per_bird = self.EXPECTED_WATER_CONSUMPTION_BY_AGE[(50, 100)]
        
        # Apply temperature adjustment
        # Research shows: 25% increase per 5°C above 20°C
        if temperature is not None and temperature > self.TEMP_BASE:
            temp_diff = temperature - self.TEMP_BASE
            temp_adjustment = 1.0 + (temp_diff / 5.0) * self.TEMP_ADJUSTMENT_PER_5C
            expected_per_bird *= temp_adjustment
        
        # Calculate total expected consumption
        if bird_count and bird_count > 0:
            expected_total = expected_per_bird * bird_count
            logger.debug(f"Expected consumption for Day {growth_day}, {bird_count} birds, {temperature}°C: "
                        f"{expected_per_bird:.4f} L/bird/day = {expected_total:.2f} L/day total")
            return expected_total
        
        return None
    
    def _determine_severity(
        self, 
        increase_ratio: float, 
        baseline_std: float, 
        current_consumption: float,
        expected_consumption: Optional[float] = None
    ) -> Optional[str]:
        """
        Determine alert severity based on increase ratio and statistical deviation
        Now uses age-adjusted baselines for more accurate detection
        
        Returns severity level or None if no anomaly detected
        """
        # Use Z-score if we have standard deviation
        if baseline_std > 0:
            baseline_value = current_consumption / increase_ratio if increase_ratio > 0 else 0
            z_score = (current_consumption - baseline_value) / baseline_std
            if z_score > 3.0:
                return 'critical'
            elif z_score > 2.5:
                return 'high'
            elif z_score > 2.0:
                return 'medium'
            elif z_score > 1.5:
                return 'low'
        
        # Ratio-based detection (now against age-adjusted expected consumption)
        if increase_ratio >= self.CRITICAL_THRESHOLD:
            return 'critical'
        elif increase_ratio >= self.HIGH_THRESHOLD:
            return 'high'
        elif increase_ratio >= self.MEDIUM_THRESHOLD:
            return 'medium'
        elif increase_ratio >= self.LOW_THRESHOLD:
            return 'low'
        
        return None
    
    def _generate_alert_message(
        self,
        current_consumption: float,
        baseline_consumption: float,
        expected_consumption: Optional[float],
        increase_percentage: float,
        severity: str,
        alert_date: date,
        growth_day: Optional[int]
    ) -> str:
        """Generate human-readable alert message with age-adjusted context"""
        severity_text = severity.upper()
        age_info = f" (Growth Day {growth_day})" if growth_day else ""
        
        message = (
            f"⚠️ {severity_text} ALERT: Abnormal water consumption detected for House {self.house.house_number}"
            f"{age_info} on {alert_date.strftime('%Y-%m-%d')}.\n\n"
            f"Current consumption: {current_consumption:.2f} L/day\n"
        )
        
        if expected_consumption:
            message += (
                f"Expected consumption (age-adjusted): {expected_consumption:.2f} L/day\n"
                f"Deviation from expected: {((current_consumption - expected_consumption) / expected_consumption * 100):.1f}%\n"
            )
        
        message += (
            f"Baseline comparison: {baseline_consumption:.2f} L/day\n"
            f"Increase: {increase_percentage:.1f}% above baseline\n\n"
            f"This may indicate:\n"
            f"- Water leak or equipment malfunction\n"
            f"- Increased bird activity or stress\n"
            f"- Environmental factors requiring attention\n"
            f"- Health issues in the flock\n\n"
            f"Please investigate immediately."
        )
        
        return message

