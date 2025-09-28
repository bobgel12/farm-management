import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
from sklearn.cluster import DBSCAN
import joblib
import os
from django.conf import settings
from django.utils import timezone
from datetime import datetime, timedelta
import logging
from rotem_scraper.models import RotemDataPoint, MLPrediction, MLModel, RotemController
from farms.models import Farm
from .models import IntegrationHealth
import json

logger = logging.getLogger(__name__)

class EnhancedMLAnalysisService:
    """Enhanced ML analysis service for integrated farms"""
    
    def __init__(self):
        self.models_dir = os.path.join(settings.BASE_DIR, 'ml_models')
        os.makedirs(self.models_dir, exist_ok=True)
        self.scaler = StandardScaler()
    
    def run_farm_analysis(self, farm_id: int):
        """Run comprehensive ML analysis for a specific farm"""
        try:
            farm = Farm.objects.get(id=farm_id)
            if not farm.has_system_integration:
                logger.info(f"Farm {farm.name} has no system integration, skipping ML analysis")
                return []
            
            logger.info(f"Starting ML analysis for farm: {farm.name}")
            results = []
            
            # Get farm-specific data
            if farm.integration_type == 'rotem':
                results.extend(self._analyze_rotem_farm(farm))
            
            # Update farm health metrics
            self._update_farm_health_metrics(farm, results)
            
            logger.info(f"ML analysis completed for farm {farm.name}. Generated {len(results)} predictions")
            return results
            
        except Farm.DoesNotExist:
            logger.error(f"Farm with ID {farm_id} not found")
            return []
        except Exception as e:
            logger.error(f"Farm ML analysis failed for farm {farm_id}: {str(e)}")
            return []
    
    def run_global_analysis(self):
        """Run ML analysis for all integrated farms"""
        logger.info("Starting global ML analysis for all integrated farms")
        all_results = []
        
        integrated_farms = Farm.objects.filter(
            has_system_integration=True,
            integration_status='active'
        )
        
        for farm in integrated_farms:
            try:
                farm_results = self.run_farm_analysis(farm.id)
                all_results.extend(farm_results)
            except Exception as e:
                logger.error(f"Failed to analyze farm {farm.name}: {str(e)}")
                continue
        
        logger.info(f"Global ML analysis completed. Generated {len(all_results)} total predictions")
        return all_results
    
    def _analyze_rotem_farm(self, farm):
        """Analyze a Rotem-integrated farm"""
        results = []
        
        try:
            # Get Rotem controllers for this farm
            controllers = RotemController.objects.filter(
                farm_id=farm.rotem_farm_id,
                is_connected=True
            )
            
            if not controllers.exists():
                logger.warning(f"No connected controllers found for farm {farm.name}")
                return results
            
            # Run analysis for each controller
            for controller in controllers:
                controller_results = self._analyze_controller(controller, farm)
                results.extend(controller_results)
            
            # Farm-level analysis
            farm_results = self._analyze_farm_level_metrics(farm, controllers)
            results.extend(farm_results)
            
        except Exception as e:
            logger.error(f"Error analyzing Rotem farm {farm.name}: {str(e)}")
        
        return results
    
    def _analyze_controller(self, controller, farm):
        """Analyze a specific controller"""
        results = []
        
        try:
            # Get recent data for this controller (last 24 hours)
            recent_data = RotemDataPoint.objects.filter(
                controller=controller,
                timestamp__gte=timezone.now() - timedelta(hours=24)
            ).order_by('timestamp')
            
            if recent_data.count() < 10:
                logger.warning(f"Insufficient data for controller {controller.controller_name}")
                return results
            
            # Anomaly detection
            anomalies = self._detect_controller_anomalies(controller, recent_data)
            results.extend(anomalies)
            
            # Failure prediction
            failures = self._predict_controller_failures(controller, recent_data)
            results.extend(failures)
            
            # Performance analysis
            performance = self._analyze_controller_performance(controller, recent_data)
            results.extend(performance)
            
        except Exception as e:
            logger.error(f"Error analyzing controller {controller.controller_name}: {str(e)}")
        
        return results
    
    def _detect_controller_anomalies(self, controller, data_points):
        """Detect anomalies in controller data"""
        try:
            if data_points.count() < 20:
                return []
            
            # Convert to DataFrame
            df = pd.DataFrame([{
                'timestamp': dp.timestamp,
                'data_type': dp.data_type,
                'value': dp.value,
                'quality': dp.quality
            } for dp in data_points])
            
            anomalies = []
            
            # Group by data type for analysis
            for data_type, group in df.groupby('data_type'):
                if len(group) < 10:
                    continue
                
                values = group['value'].values.reshape(-1, 1)
                
                # Train Isolation Forest
                iso_forest = IsolationForest(
                    contamination=0.1,
                    random_state=42,
                    n_estimators=100
                )
                
                try:
                    anomaly_scores = iso_forest.fit_predict(values)
                    scores = iso_forest.score_samples(values)
                    
                    # Find anomalies
                    anomaly_indices = np.where(anomaly_scores == -1)[0]
                    
                    for idx in anomaly_indices:
                        anomaly_data = group.iloc[idx]
                        score = scores[idx]
                        
                        prediction = MLPrediction.objects.create(
                            controller=controller,
                            prediction_type='anomaly',
                            predicted_at=timezone.now(),
                            confidence_score=abs(score),
                            prediction_data={
                                'data_type': data_type,
                                'value': float(anomaly_data['value']),
                                'timestamp': anomaly_data['timestamp'].isoformat(),
                                'anomaly_score': float(score),
                                'severity': 'high' if abs(score) > 0.5 else 'medium' if abs(score) > 0.3 else 'low',
                                'farm_name': controller.farm.name if hasattr(controller, 'farm') else 'Unknown'
                            }
                        )
                        anomalies.append(prediction)
                        
                        logger.info(f"Anomaly detected in {controller.controller_name}: {data_type} = {anomaly_data['value']} (score: {score:.3f})")
                
                except Exception as e:
                    logger.error(f"Error in anomaly detection for {data_type}: {str(e)}")
                    continue
            
            return anomalies
            
        except Exception as e:
            logger.error(f"Anomaly detection failed for controller {controller.controller_name}: {str(e)}")
            return []
    
    def _predict_controller_failures(self, controller, data_points):
        """Predict potential controller failures"""
        try:
            if data_points.count() < 50:
                return []
            
            # Calculate failure indicators
            indicators = self._calculate_failure_indicators(data_points)
            failure_probability = self._calculate_failure_probability(indicators)
            
            if failure_probability > 0.3:  # 30% threshold
                prediction = MLPrediction.objects.create(
                    controller=controller,
                    prediction_type='failure',
                    predicted_at=timezone.now(),
                    confidence_score=failure_probability,
                    prediction_data={
                        'failure_probability': failure_probability,
                        'indicators': indicators,
                        'predicted_failure_time': (timezone.now() + timedelta(hours=24)).isoformat(),
                        'recommended_actions': self._get_failure_recommendations(indicators),
                        'farm_name': controller.farm.name if hasattr(controller, 'farm') else 'Unknown'
                    }
                )
                
                logger.info(f"Failure prediction for {controller.controller_name}: {failure_probability:.2%} probability")
                return [prediction]
            
            return []
            
        except Exception as e:
            logger.error(f"Failure prediction failed for controller {controller.controller_name}: {str(e)}")
            return []
    
    def _analyze_controller_performance(self, controller, data_points):
        """Analyze controller performance"""
        try:
            if data_points.count() < 10:
                return []
            
            # Calculate performance metrics
            total_points = data_points.count()
            good_quality = data_points.filter(quality='good').count()
            warning_quality = data_points.filter(quality='warning').count()
            error_quality = data_points.filter(quality='error').count()
            
            performance_score = (good_quality + 0.5 * warning_quality) / total_points if total_points > 0 else 0
            
            # Data completeness (assuming 5-minute intervals)
            expected_points = 24 * 12  # 24 hours * 12 points per hour
            data_completeness = min(total_points / expected_points, 1.0) if expected_points > 0 else 0
            
            # Overall efficiency
            efficiency_score = (performance_score + data_completeness) / 2
            
            prediction = MLPrediction.objects.create(
                controller=controller,
                prediction_type='performance',
                predicted_at=timezone.now(),
                confidence_score=efficiency_score,
                prediction_data={
                    'performance_score': performance_score,
                    'data_completeness': data_completeness,
                    'efficiency_score': efficiency_score,
                    'total_data_points': total_points,
                    'good_quality_points': good_quality,
                    'warning_quality_points': warning_quality,
                    'error_quality_points': error_quality,
                    'recommendations': self._get_performance_recommendations(efficiency_score, data_completeness),
                    'farm_name': controller.farm.name if hasattr(controller, 'farm') else 'Unknown'
                }
            )
            
            logger.info(f"Performance analysis for {controller.controller_name}: {efficiency_score:.2%} efficiency")
            return [prediction]
            
        except Exception as e:
            logger.error(f"Performance analysis failed for controller {controller.controller_name}: {str(e)}")
            return []
    
    def _analyze_farm_level_metrics(self, farm, controllers):
        """Analyze farm-level metrics and optimizations"""
        try:
            results = []
            
            # Get all data from farm controllers
            all_data = RotemDataPoint.objects.filter(
                controller__in=controllers,
                timestamp__gte=timezone.now() - timedelta(hours=24)
            )
            
            if all_data.count() < 50:
                logger.warning(f"Insufficient data for farm-level analysis of {farm.name}")
                return results
            
            # Environmental optimization
            env_optimization = self._analyze_environmental_optimization(farm, all_data)
            results.extend(env_optimization)
            
            # Farm efficiency analysis
            efficiency_analysis = self._analyze_farm_efficiency(farm, all_data)
            results.extend(efficiency_analysis)
            
            return results
            
        except Exception as e:
            logger.error(f"Farm-level analysis failed for {farm.name}: {str(e)}")
            return []
    
    def _analyze_environmental_optimization(self, farm, data_points):
        """Analyze environmental conditions and suggest optimizations"""
        try:
            # Get temperature and humidity data
            temp_data = data_points.filter(data_type__contains='temperature')
            humidity_data = data_points.filter(data_type__contains='humidity')
            
            if not temp_data.exists() or not humidity_data.exists():
                return []
            
            # Calculate averages
            temp_values = [dp.value for dp in temp_data if dp.value is not None]
            humidity_values = [dp.value for dp in humidity_data if dp.value is not None]
            
            if not temp_values or not humidity_values:
                return []
            
            temp_mean = np.mean(temp_values)
            temp_std = np.std(temp_values)
            humidity_mean = np.mean(humidity_values)
            humidity_std = np.std(humidity_values)
            
            # Optimal ranges for poultry
            optimal_temp_range = (20, 25)  # Celsius
            optimal_humidity_range = (50, 70)  # Percentage
            
            suggestions = []
            
            # Temperature analysis
            if temp_mean < optimal_temp_range[0]:
                suggestions.append({
                    'type': 'temperature',
                    'current': temp_mean,
                    'optimal_range': optimal_temp_range,
                    'action': 'Increase heating or reduce ventilation',
                    'priority': 'high' if temp_mean < optimal_temp_range[0] - 2 else 'medium'
                })
            elif temp_mean > optimal_temp_range[1]:
                suggestions.append({
                    'type': 'temperature',
                    'current': temp_mean,
                    'optimal_range': optimal_temp_range,
                    'action': 'Increase ventilation or reduce heating',
                    'priority': 'high' if temp_mean > optimal_temp_range[1] + 2 else 'medium'
                })
            
            # Humidity analysis
            if humidity_mean < optimal_humidity_range[0]:
                suggestions.append({
                    'type': 'humidity',
                    'current': humidity_mean,
                    'optimal_range': optimal_humidity_range,
                    'action': 'Increase humidity with misting or reduce ventilation',
                    'priority': 'medium'
                })
            elif humidity_mean > optimal_humidity_range[1]:
                suggestions.append({
                    'type': 'humidity',
                    'current': humidity_mean,
                    'optimal_range': optimal_humidity_range,
                    'action': 'Increase ventilation or use dehumidifier',
                    'priority': 'high' if humidity_mean > optimal_humidity_range[1] + 10 else 'medium'
                })
            
            # Stability analysis
            if temp_std > 2:
                suggestions.append({
                    'type': 'temperature_stability',
                    'current_std': temp_std,
                    'optimal_std': 1.0,
                    'action': 'Improve temperature control system stability',
                    'priority': 'high'
                })
            
            if humidity_std > 10:
                suggestions.append({
                    'type': 'humidity_stability',
                    'current_std': humidity_std,
                    'optimal_std': 5.0,
                    'action': 'Improve humidity control system stability',
                    'priority': 'medium'
                })
            
            # Create prediction records
            results = []
            for suggestion in suggestions:
                # Use the first controller as representative
                controller = data_points.first().controller
                
                prediction = MLPrediction.objects.create(
                    controller=controller,
                    prediction_type='optimization',
                    predicted_at=timezone.now(),
                    confidence_score=0.8,
                    prediction_data={
                        **suggestion,
                        'farm_name': farm.name,
                        'analysis_type': 'environmental_optimization'
                    }
                )
                results.append(prediction)
            
            return results
            
        except Exception as e:
            logger.error(f"Environmental optimization analysis failed for {farm.name}: {str(e)}")
            return []
    
    def _analyze_farm_efficiency(self, farm, data_points):
        """Analyze overall farm efficiency"""
        try:
            # Calculate efficiency metrics
            total_points = data_points.count()
            good_quality = data_points.filter(quality='good').count()
            warning_quality = data_points.filter(quality='warning').count()
            error_quality = data_points.filter(quality='error').count()
            
            data_quality_score = (good_quality + 0.5 * warning_quality) / total_points if total_points > 0 else 0
            
            # Data completeness
            expected_points = 24 * 12 * len(data_points.values_list('controller', flat=True).distinct())
            data_completeness = min(total_points / expected_points, 1.0) if expected_points > 0 else 0
            
            # Overall farm efficiency
            farm_efficiency = (data_quality_score + data_completeness) / 2
            
            # Create farm efficiency prediction
            controller = data_points.first().controller
            
            prediction = MLPrediction.objects.create(
                controller=controller,
                prediction_type='farm_efficiency',
                predicted_at=timezone.now(),
                confidence_score=farm_efficiency,
                prediction_data={
                    'farm_name': farm.name,
                    'data_quality_score': data_quality_score,
                    'data_completeness': data_completeness,
                    'farm_efficiency': farm_efficiency,
                    'total_data_points': total_points,
                    'good_quality_points': good_quality,
                    'warning_quality_points': warning_quality,
                    'error_quality_points': error_quality,
                    'recommendations': self._get_farm_efficiency_recommendations(farm_efficiency, data_completeness),
                    'analysis_type': 'farm_efficiency'
                }
            )
            
            logger.info(f"Farm efficiency analysis for {farm.name}: {farm_efficiency:.2%} efficiency")
            return [prediction]
            
        except Exception as e:
            logger.error(f"Farm efficiency analysis failed for {farm.name}: {str(e)}")
            return []
    
    def _calculate_failure_indicators(self, data_points):
        """Calculate failure indicators from data points"""
        indicators = {}
        
        # Convert to DataFrame
        df = pd.DataFrame([{
            'timestamp': dp.timestamp,
            'data_type': dp.data_type,
            'value': dp.value,
            'quality': dp.quality
        } for dp in data_points])
        
        # Error rate
        total_points = len(df)
        error_points = len(df[df['quality'] == 'error'])
        indicators['error_rate'] = error_points / total_points if total_points > 0 else 0
        
        # Warning rate
        warning_points = len(df[df['quality'] == 'warning'])
        indicators['warning_rate'] = warning_points / total_points if total_points > 0 else 0
        
        # Temperature variance (if temperature data exists)
        temp_data = df[df['data_type'].str.contains('temperature', case=False)]
        if len(temp_data) > 0:
            temp_values = temp_data['value'].values
            temp_mean = np.mean(temp_values)
            temp_std = np.std(temp_values)
            indicators['temperature_variance'] = temp_std / temp_mean if temp_mean != 0 else 0
            
            # Extreme temperature rate
            extreme_temp_count = len(temp_data[(temp_data['value'] < temp_mean - 3*temp_std) | 
                                            (temp_data['value'] > temp_mean + 3*temp_std)])
            indicators['extreme_temperature_rate'] = extreme_temp_count / len(temp_data) if len(temp_data) > 0 else 0
        
        # Humidity variance
        humidity_data = df[df['data_type'].str.contains('humidity', case=False)]
        if len(humidity_data) > 0:
            humidity_values = humidity_data['value'].values
            indicators['humidity_variance'] = np.std(humidity_values) / np.mean(humidity_values) if np.mean(humidity_values) != 0 else 0
        
        # Data gaps
        if len(df) > 1:
            df_sorted = df.sort_values('timestamp')
            time_diffs = df_sorted['timestamp'].diff().dt.total_seconds() / 60  # minutes
            large_gaps = len(time_diffs[time_diffs > 30])  # gaps > 30 minutes
            indicators['data_gap_rate'] = large_gaps / len(time_diffs) if len(time_diffs) > 0 else 0
        
        return indicators
    
    def _calculate_failure_probability(self, indicators):
        """Calculate failure probability based on indicators"""
        weights = {
            'error_rate': 0.3,
            'warning_rate': 0.2,
            'temperature_variance': 0.2,
            'extreme_temperature_rate': 0.15,
            'humidity_variance': 0.1,
            'data_gap_rate': 0.05
        }
        
        total_score = 0
        total_weight = 0
        
        for indicator, weight in weights.items():
            if indicator in indicators:
                normalized_value = min(indicators[indicator], 1.0)
                total_score += normalized_value * weight
                total_weight += weight
        
        return total_score / total_weight if total_weight > 0 else 0
    
    def _get_failure_recommendations(self, indicators):
        """Get recommendations based on failure indicators"""
        recommendations = []
        
        if indicators.get('error_rate', 0) > 0.1:
            recommendations.append("High error rate detected - check sensor connections and calibration")
        
        if indicators.get('temperature_variance', 0) > 0.5:
            recommendations.append("High temperature variance - check heating/cooling systems")
        
        if indicators.get('extreme_temperature_rate', 0) > 0.1:
            recommendations.append("Extreme temperature readings - inspect temperature sensors")
        
        if indicators.get('data_gap_rate', 0) > 0.2:
            recommendations.append("Frequent data gaps - check network connectivity and controller status")
        
        if not recommendations:
            recommendations.append("Monitor system closely for any unusual patterns")
        
        return recommendations
    
    def _get_performance_recommendations(self, efficiency_score, data_completeness):
        """Get recommendations based on performance metrics"""
        recommendations = []
        
        if efficiency_score < 0.7:
            recommendations.append("System performance is below optimal - investigate data quality issues")
        
        if data_completeness < 0.8:
            recommendations.append("Data collection completeness is low - check scraper frequency and reliability")
        
        if efficiency_score > 0.9:
            recommendations.append("System is performing excellently - maintain current monitoring levels")
        
        return recommendations
    
    def _get_farm_efficiency_recommendations(self, farm_efficiency, data_completeness):
        """Get recommendations for farm efficiency"""
        recommendations = []
        
        if farm_efficiency < 0.7:
            recommendations.append("Farm efficiency is below optimal - review system integration and data quality")
        
        if data_completeness < 0.8:
            recommendations.append("Data collection completeness is low - check integration health and sync frequency")
        
        if farm_efficiency > 0.9:
            recommendations.append("Farm is operating at excellent efficiency - maintain current practices")
        
        return recommendations
    
    def _update_farm_health_metrics(self, farm, analysis_results):
        """Update farm health metrics based on analysis results"""
        try:
            # Calculate health score based on analysis results
            if not analysis_results:
                health_score = 0.5  # Neutral if no data
            else:
                # Calculate average confidence score
                confidence_scores = [result.confidence_score for result in analysis_results if hasattr(result, 'confidence_score')]
                health_score = np.mean(confidence_scores) if confidence_scores else 0.5
            
            # Update integration health
            health, created = IntegrationHealth.objects.get_or_create(
                farm=farm,
                integration_type=farm.integration_type,
                defaults={
                    'is_healthy': health_score > 0.7,
                    'last_checked': timezone.now(),
                    'success_rate_24h': health_score * 100,
                    'consecutive_failures': 0 if health_score > 0.7 else 1,
                    'average_response_time': 1.0,  # Placeholder
                    'error_details': json.dumps({
                        'last_analysis': timezone.now().isoformat(),
                        'analysis_results_count': len(analysis_results),
                        'health_score': health_score
                    })
                }
            )
            
            if not created:
                health.is_healthy = health_score > 0.7
                health.last_checked = timezone.now()
                health.success_rate_24h = health_score * 100
                health.consecutive_failures = 0 if health_score > 0.7 else health.consecutive_failures + 1
                health.error_details = json.dumps({
                    'last_analysis': timezone.now().isoformat(),
                    'analysis_results_count': len(analysis_results),
                    'health_score': health_score
                })
                health.save()
            
            logger.info(f"Updated health metrics for farm {farm.name}: health_score={health_score:.2f}")
            
        except Exception as e:
            logger.error(f"Failed to update health metrics for farm {farm.name}: {str(e)}")
