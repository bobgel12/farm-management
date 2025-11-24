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
from ..models import RotemDataPoint, MLPrediction, MLModel, RotemController, RotemDailySummary
import json

logger = logging.getLogger(__name__)

class MLAnalysisService:
    def __init__(self):
        self.models_dir = os.path.join(settings.BASE_DIR, 'ml_models')
        os.makedirs(self.models_dir, exist_ok=True)
        self.scaler = StandardScaler()
    
    def run_analysis(self):
        """Run all ML analysis tasks"""
        logger.info("Starting comprehensive ML analysis")
        results = []
        
        try:
            # Anomaly detection
            logger.info("Running anomaly detection...")
            anomaly_results = self.detect_anomalies()
            results.extend(anomaly_results)
            
            # Equipment failure prediction
            logger.info("Running equipment failure prediction...")
            failure_predictions = self.predict_equipment_failure()
            results.extend(failure_predictions)
            
            # Environmental optimization
            logger.info("Running environmental optimization...")
            optimization_suggestions = self.optimize_environment()
            results.extend(optimization_suggestions)
            
            # Performance analysis
            logger.info("Running performance analysis...")
            performance_analysis = self.analyze_performance()
            results.extend(performance_analysis)
            
            logger.info(f"ML analysis completed. Generated {len(results)} predictions")
            return results
            
        except Exception as e:
            logger.error(f"ML analysis failed: {str(e)}")
            raise
    
    def detect_anomalies(self):
        """Detect anomalous patterns in sensor data using Isolation Forest"""
        try:
            # Get recent data (last 24 hours)
            recent_data = RotemDataPoint.objects.filter(
                timestamp__gte=timezone.now() - timedelta(hours=24)
            ).values('controller', 'data_type', 'value', 'timestamp', 'unit')
            
            if not recent_data:
                logger.warning("No recent data available for anomaly detection")
                return []
            
            # Convert to DataFrame
            df = pd.DataFrame(list(recent_data))
            
            # Group by controller and data type for analysis
            anomalies = []
            for (controller_id, data_type), group in df.groupby(['controller', 'data_type']):
                if len(group) < 10:  # Need sufficient data points
                    continue
                
                # Prepare data for anomaly detection
                values = group['value'].values.reshape(-1, 1)
                timestamps = group['timestamp'].values
                
                # Train Isolation Forest
                contamination = 0.1  # Expect 10% anomalies
                iso_forest = IsolationForest(
                    contamination=contamination, 
                    random_state=42,
                    n_estimators=100
                )
                
                try:
                    anomaly_scores = iso_forest.fit_predict(values)
                    scores = iso_forest.score_samples(values)
                    
                    # Find anomalies (score = -1)
                    anomaly_indices = np.where(anomaly_scores == -1)[0]
                    
                    for idx in anomaly_indices:
                        anomaly_data = group.iloc[idx]
                        score = scores[idx]
                        
                        # Get controller object
                        try:
                            controller = RotemController.objects.get(id=controller_id)
                        except RotemController.DoesNotExist:
                            continue
                        
                        # Create prediction record
                        prediction = MLPrediction.objects.create(
                            controller=controller,
                            prediction_type='anomaly',
                            predicted_at=timezone.now(),
                            confidence_score=abs(score),
                            prediction_data={
                                'data_type': data_type,
                                'value': float(anomaly_data['value']),
                                'unit': anomaly_data['unit'],
                                'timestamp': anomaly_data['timestamp'].isoformat(),
                                'anomaly_score': float(score),
                                'severity': 'high' if abs(score) > 0.5 else 'medium' if abs(score) > 0.3 else 'low'
                            }
                        )
                        anomalies.append(prediction)
                        
                        logger.info(f"Anomaly detected: {data_type} = {anomaly_data['value']} {anomaly_data['unit']} (score: {score:.3f})")
                
                except Exception as e:
                    logger.error(f"Error in anomaly detection for {data_type}: {str(e)}")
                    continue
            
            logger.info(f"Detected {len(anomalies)} anomalies")
            return anomalies
            
        except Exception as e:
            logger.error(f"Anomaly detection failed: {str(e)}")
            return []
    
    def predict_equipment_failure(self):
        """Predict potential equipment failures using multiple indicators"""
        try:
            controllers = RotemController.objects.filter(is_connected=True)
            predictions = []
            
            for controller in controllers:
                # Get recent data for this controller (last 7 days)
                recent_data = RotemDataPoint.objects.filter(
                    controller=controller,
                    timestamp__gte=timezone.now() - timedelta(days=7)
                ).order_by('timestamp')
                
                if recent_data.count() < 50:  # Need sufficient data
                    continue
                
                # Calculate failure indicators
                failure_indicators = self._calculate_failure_indicators(recent_data)
                
                # Predict failure based on indicators
                failure_probability = self._calculate_failure_probability(failure_indicators)
                
                if failure_probability > 0.3:  # 30% threshold
                    prediction = MLPrediction.objects.create(
                        controller=controller,
                        prediction_type='failure',
                        predicted_at=timezone.now(),
                        confidence_score=failure_probability,
                        prediction_data={
                            'failure_probability': failure_probability,
                            'indicators': failure_indicators,
                            'predicted_failure_time': (timezone.now() + timedelta(hours=24)).isoformat(),
                            'recommended_actions': self._get_failure_recommendations(failure_indicators)
                        }
                    )
                    predictions.append(prediction)
                    
                    logger.info(f"Failure prediction for {controller.controller_name}: {failure_probability:.2%} probability")
            
            logger.info(f"Generated {len(predictions)} failure predictions")
            return predictions
            
        except Exception as e:
            logger.error(f"Equipment failure prediction failed: {str(e)}")
            return []
    
    def _calculate_failure_indicators(self, data_points):
        """Calculate various failure indicators from sensor data"""
        indicators = {}
        
        # Convert to DataFrame for easier analysis
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
        
        # Data quality issues
        warning_points = len(df[df['quality'] == 'warning'])
        indicators['warning_rate'] = warning_points / total_points if total_points > 0 else 0
        
        # Temperature anomalies (if temperature data exists)
        temp_data = df[df['data_type'].str.contains('temperature', case=False)]
        if len(temp_data) > 0:
            temp_values = temp_data['value'].values
            temp_mean = np.mean(temp_values)
            temp_std = np.std(temp_values)
            indicators['temperature_variance'] = temp_std / temp_mean if temp_mean != 0 else 0
            
            # Check for extreme temperatures
            extreme_temp_count = len(temp_data[(temp_data['value'] < temp_mean - 3*temp_std) | 
                                            (temp_data['value'] > temp_mean + 3*temp_std)])
            indicators['extreme_temperature_rate'] = extreme_temp_count / len(temp_data) if len(temp_data) > 0 else 0
        
        # Humidity anomalies
        humidity_data = df[df['data_type'].str.contains('humidity', case=False)]
        if len(humidity_data) > 0:
            humidity_values = humidity_data['value'].values
            indicators['humidity_variance'] = np.std(humidity_values) / np.mean(humidity_values) if np.mean(humidity_values) != 0 else 0
        
        # Data gaps (missing data)
        if len(df) > 1:
            df_sorted = df.sort_values('timestamp')
            time_diffs = df_sorted['timestamp'].diff().dt.total_seconds() / 60  # minutes
            large_gaps = len(time_diffs[time_diffs > 30])  # gaps > 30 minutes
            indicators['data_gap_rate'] = large_gaps / len(time_diffs) if len(time_diffs) > 0 else 0
        
        return indicators
    
    def _calculate_failure_probability(self, indicators):
        """Calculate failure probability based on indicators"""
        # Weighted scoring system
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
                # Normalize indicator to 0-1 scale
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
    
    def optimize_environment(self):
        """Suggest environmental optimizations based on sensor data"""
        try:
            # Get temperature and humidity data from all houses
            temp_data = RotemDataPoint.objects.filter(
                data_type__contains='temperature',
                timestamp__gte=timezone.now() - timedelta(hours=24)
            ).values('value', 'timestamp', 'data_type')
            
            humidity_data = RotemDataPoint.objects.filter(
                data_type__contains='humidity',
                timestamp__gte=timezone.now() - timedelta(hours=24)
            ).values('value', 'timestamp', 'data_type')
            
            if not temp_data or not humidity_data:
                logger.warning("Insufficient data for environmental optimization")
                return []
            
            # Analyze temperature patterns
            temp_df = pd.DataFrame(list(temp_data))
            humidity_df = pd.DataFrame(list(humidity_data))
            
            # Calculate optimal ranges for poultry
            temp_values = temp_df['value'].values
            humidity_values = humidity_df['value'].values
            
            temp_mean = np.mean(temp_values)
            temp_std = np.std(temp_values)
            humidity_mean = np.mean(humidity_values)
            humidity_std = np.std(humidity_values)
            
            # Optimal ranges for poultry (adjust based on age/breed)
            optimal_temp_range = (20, 25)  # Celsius
            optimal_humidity_range = (50, 70)  # Percentage
            
            suggestions = []
            predictions = []
            
            # Temperature optimization
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
            
            # Humidity optimization
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
            
            # Temperature stability
            if temp_std > 2:  # High temperature variation
                suggestions.append({
                    'type': 'temperature_stability',
                    'current_std': temp_std,
                    'optimal_std': 1.0,
                    'action': 'Improve temperature control system stability',
                    'priority': 'high'
                })
            
            # Humidity stability
            if humidity_std > 10:  # High humidity variation
                suggestions.append({
                    'type': 'humidity_stability',
                    'current_std': humidity_std,
                    'optimal_std': 5.0,
                    'action': 'Improve humidity control system stability',
                    'priority': 'medium'
                })
            
            # Create prediction records for each suggestion
            for suggestion in suggestions:
                # Get a representative controller
                controller = RotemController.objects.filter(is_connected=True).first()
                if not controller:
                    continue
                
                prediction = MLPrediction.objects.create(
                    controller=controller,
                    prediction_type='optimization',
                    predicted_at=timezone.now(),
                    confidence_score=0.8,  # High confidence for environmental recommendations
                    prediction_data=suggestion
                )
                predictions.append(prediction)
            
            logger.info(f"Generated {len(predictions)} optimization suggestions")
            return predictions
            
        except Exception as e:
            logger.error(f"Environmental optimization failed: {str(e)}")
            return []
    
    def analyze_performance(self):
        """Analyze overall system performance and efficiency"""
        try:
            # Get data from last 24 hours
            recent_data = RotemDataPoint.objects.filter(
                timestamp__gte=timezone.now() - timedelta(hours=24)
            ).values('data_type', 'value', 'quality', 'timestamp')
            
            if not recent_data:
                return []
            
            df = pd.DataFrame(list(recent_data))
            
            # Calculate performance metrics
            total_points = len(df)
            good_quality = len(df[df['quality'] == 'good'])
            warning_quality = len(df[df['quality'] == 'warning'])
            error_quality = len(df[df['quality'] == 'error'])
            
            performance_score = (good_quality + 0.5 * warning_quality) / total_points if total_points > 0 else 0
            
            # Data completeness
            expected_points = 24 * 12  # 24 hours * 12 points per hour (5-minute intervals)
            data_completeness = min(total_points / expected_points, 1.0) if expected_points > 0 else 0
            
            # System efficiency score
            efficiency_score = (performance_score + data_completeness) / 2
            
            # Create performance prediction
            controller = RotemController.objects.filter(is_connected=True).first()
            if not controller:
                return []
            
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
                    'recommendations': self._get_performance_recommendations(efficiency_score, data_completeness)
                }
            )
            
            logger.info(f"Performance analysis completed. Efficiency score: {efficiency_score:.2%}")
            return [prediction]
            
        except Exception as e:
            logger.error(f"Performance analysis failed: {str(e)}")
            return []
    
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
    
    def train_models(self):
        """Train and save ML models for future use"""
        try:
            # Try to use aggregated data first (more efficient)
            use_aggregated = True
            training_data = None
            
            # Check if we have aggregated summaries for the last 30 days
            cutoff_date = timezone.now().date() - timedelta(days=30)
            summary_count = RotemDailySummary.objects.filter(date__gte=cutoff_date).count()
            
            if summary_count >= 30:  # At least 30 days of aggregated data
                logger.info("Using aggregated daily summaries for model training")
                summaries = RotemDailySummary.objects.filter(
                    date__gte=cutoff_date
                ).select_related('controller')
                
                # Convert summaries to training format
                training_records = []
                for summary in summaries:
                    # Use average values as representative data points
                    if summary.temperature_avg is not None:
                        training_records.append({
                            'data_type': 'temperature',
                            'value': summary.temperature_avg,
                            'quality': 'good' if summary.anomalies_count == 0 else 'warning',
                            'timestamp': timezone.make_aware(
                                timezone.datetime.combine(summary.date, timezone.datetime.min.time())
                            ),
                            'controller_id': summary.controller.id,
                        })
                    if summary.humidity_avg is not None:
                        training_records.append({
                            'data_type': 'humidity',
                            'value': summary.humidity_avg,
                            'quality': 'good' if summary.anomalies_count == 0 else 'warning',
                            'timestamp': timezone.make_aware(
                                timezone.datetime.combine(summary.date, timezone.datetime.min.time())
                            ),
                            'controller_id': summary.controller.id,
                        })
                    if summary.static_pressure_avg is not None:
                        training_records.append({
                            'data_type': 'static_pressure',
                            'value': summary.static_pressure_avg,
                            'quality': 'good' if summary.anomalies_count == 0 else 'warning',
                            'timestamp': timezone.make_aware(
                                timezone.datetime.combine(summary.date, timezone.datetime.min.time())
                            ),
                            'controller_id': summary.controller.id,
                        })
                
                training_data = training_records
                logger.info(f"Using {len(training_records)} aggregated data points for training")
            else:
                use_aggregated = False
                logger.info("Insufficient aggregated data, falling back to raw data points")
            
            # Fallback to raw data points if aggregated data is insufficient
            if not use_aggregated or len(training_data) < 1000:
                logger.info("Fetching raw data points for training")
                training_data = RotemDataPoint.objects.filter(
                    timestamp__gte=timezone.now() - timedelta(days=30)
                ).values('data_type', 'value', 'quality', 'timestamp', 'controller_id')
            
            if len(training_data) < 1000:
                logger.warning("Insufficient data for model training")
                return False
            
            # Convert to DataFrame
            if isinstance(training_data, list):
                df = pd.DataFrame(training_data)
            else:
                df = pd.DataFrame(list(training_data))
            
            # Train anomaly detection model
            self._train_anomaly_model(df)
            
            # Train failure prediction model
            self._train_failure_model(df)
            
            logger.info("Model training completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Model training failed: {str(e)}")
            return False
    
    def _train_anomaly_model(self, df):
        """Train anomaly detection model"""
        # This is a simplified example - in practice, you'd use more sophisticated features
        numeric_data = df[df['data_type'].isin(['temperature', 'humidity', 'pressure'])]
        
        if len(numeric_data) < 100:
            return
        
        # Prepare features
        features = numeric_data[['value']].values
        
        # Train Isolation Forest
        model = IsolationForest(contamination=0.1, random_state=42)
        model.fit(features)
        
        # Save model
        model_path = os.path.join(self.models_dir, 'anomaly_model.joblib')
        joblib.dump(model, model_path)
        
        # Save model metadata
        MLModel.objects.update_or_create(
            name='anomaly_detection',
            defaults={
                'version': '1.0',
                'model_type': 'isolation_forest',
                'is_active': True,
                'accuracy_score': 0.85,  # Placeholder
                'training_data_size': len(features),
                'last_trained': timezone.now(),
                'model_file_path': model_path
            }
        )
    
    def _train_failure_model(self, df):
        """Train failure prediction model"""
        # This is a simplified example - in practice, you'd use more sophisticated features
        # and proper feature engineering
        
        # Create failure labels based on error rates
        df['error_rate'] = df.groupby('data_type')['quality'].transform(
            lambda x: (x == 'error').rolling(window=10).mean()
        )
        
        # Prepare features and labels
        features = df[['value', 'error_rate']].fillna(0).values
        labels = (df['error_rate'] > 0.1).astype(int).values
        
        if len(np.unique(labels)) < 2:
            return
        
        # Train Random Forest
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(features, labels)
        
        # Save model
        model_path = os.path.join(self.models_dir, 'failure_model.joblib')
        joblib.dump(model, model_path)
        
        # Save model metadata
        MLModel.objects.update_or_create(
            name='failure_prediction',
            defaults={
                'version': '1.0',
                'model_type': 'random_forest',
                'is_active': True,
                'accuracy_score': 0.75,  # Placeholder
                'training_data_size': len(features),
                'last_trained': timezone.now(),
                'model_file_path': model_path
            }
        )