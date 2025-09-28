import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import joblib
import os
from django.conf import settings
from django.utils import timezone
from ..models import RotemDataPoint, MLPrediction, MLModel
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class MLAnalysisService:
    def __init__(self):
        self.models_dir = os.path.join(settings.BASE_DIR, 'ml_models')
        os.makedirs(self.models_dir, exist_ok=True)
    
    def run_analysis(self):
        """Run all ML analysis tasks"""
        results = []
        
        # Anomaly detection
        anomaly_results = self.detect_anomalies()
        results.extend(anomaly_results)
        
        # Equipment failure prediction
        failure_predictions = self.predict_equipment_failure()
        results.extend(failure_predictions)
        
        # Environmental optimization
        optimization_suggestions = self.optimize_environment()
        results.extend(optimization_suggestions)
        
        return results
    
    def detect_anomalies(self):
        """Detect anomalous patterns in sensor data"""
        # Get recent data
        recent_data = RotemDataPoint.objects.filter(
            timestamp__gte=timezone.now() - timedelta(hours=24)
        ).values('controller', 'data_type', 'value', 'timestamp')
        
        if not recent_data:
            return []
        
        # Convert to DataFrame
        df = pd.DataFrame(list(recent_data))
        
        # Group by controller and data type
        anomalies = []
        for (controller_id, data_type), group in df.groupby(['controller', 'data_type']):
            values = group['value'].values.reshape(-1, 1)
            
            # Train isolation forest
            iso_forest = IsolationForest(contamination=0.1, random_state=42)
            anomaly_scores = iso_forest.fit_predict(values)
            
            # Find anomalies
            anomaly_indices = np.where(anomaly_scores == -1)[0]
            
            for idx in anomaly_indices:
                anomaly_data = group.iloc[idx]
                
                # Save prediction
                prediction = MLPrediction.objects.create(
                    controller_id=controller_id,
                    prediction_type='anomaly',
                    predicted_at=timezone.now(),
                    confidence_score=abs(iso_forest.score_samples(values[idx].reshape(1, -1))[0]),
                    prediction_data={
                        'data_type': data_type,
                        'value': anomaly_data['value'],
                        'timestamp': anomaly_data['timestamp'].isoformat(),
                        'anomaly_score': iso_forest.score_samples(values[idx].reshape(1, -1))[0]
                    }
                )
                anomalies.append(prediction)
        
        logger.info(f"Detected {len(anomalies)} anomalies")
        return anomalies
    
    def predict_equipment_failure(self):
        """Predict potential equipment failures"""
        # This is a simplified example - in practice, you'd use more sophisticated models
        controllers = RotemController.objects.filter(is_connected=True)
        predictions = []
        
        for controller in controllers:
            # Get recent data for this controller
            recent_data = RotemDataPoint.objects.filter(
                controller=controller,
                timestamp__gte=timezone.now() - timedelta(days=7)
            ).order_by('timestamp')
            
            if recent_data.count() < 100:  # Need sufficient data
                continue
            
            # Simple heuristic: high error rate or unusual patterns
            error_count = recent_data.filter(quality='error').count()
            total_count = recent_data.count()
            error_rate = error_count / total_count if total_count > 0 else 0
            
            # Predict failure if error rate is high
            if error_rate > 0.1:  # 10% error rate threshold
                prediction = MLPrediction.objects.create(
                    controller=controller,
                    prediction_type='failure',
                    predicted_at=timezone.now(),
                    confidence_score=min(error_rate * 2, 1.0),  # Scale to 0-1
                    prediction_data={
                        'error_rate': error_rate,
                        'error_count': error_count,
                        'total_count': total_count,
                        'predicted_failure_time': (timezone.now() + timedelta(hours=24)).isoformat()
                    }
                )
                predictions.append(prediction)
        
        logger.info(f"Generated {len(predictions)} failure predictions")
        return predictions
    
    def optimize_environment(self):
        """Suggest environmental optimizations"""
        # Get temperature and humidity data
        temp_data = RotemDataPoint.objects.filter(
            data_type='temperature',
            timestamp__gte=timezone.now() - timedelta(hours=24)
        ).values('value', 'timestamp')
        
        humidity_data = RotemDataPoint.objects.filter(
            data_type='humidity',
            timestamp__gte=timezone.now() - timedelta(hours=24)
        ).values('value', 'timestamp')
        
        if not temp_data or not humidity_data:
            return []
        
        # Calculate optimal ranges
        temp_values = [d['value'] for d in temp_data]
        humidity_values = [d['value'] for d in humidity_data]
        
        temp_mean = np.mean(temp_values)
        humidity_mean = np.mean(humidity_values)
        
        # Simple optimization suggestions
        suggestions = []
        
        if temp_mean > 25:  # Too hot
            suggestions.append({
                'type': 'temperature',
                'current': temp_mean,
                'recommended': 22,
                'action': 'Increase ventilation or reduce heating'
            })
        
        if humidity_mean > 70:  # Too humid
            suggestions.append({
                'type': 'humidity',
                'current': humidity_mean,
                'recommended': 60,
                'action': 'Increase ventilation or use dehumidifier'
            })
        
        # Save optimization predictions
        predictions = []
        for suggestion in suggestions:
            # Get first controller for optimization suggestions
            controller = RotemController.objects.filter(is_connected=True).first()
            if controller:
                prediction = MLPrediction.objects.create(
                    controller=controller,
                    prediction_type='optimization',
                    predicted_at=timezone.now(),
                    confidence_score=0.8,
                    prediction_data=suggestion
                )
                predictions.append(prediction)
        
        logger.info(f"Generated {len(predictions)} optimization suggestions")
        return predictions
