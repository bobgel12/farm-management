"""Multivariate anomaly detection using persisted Isolation Forest models."""
from __future__ import annotations

import logging
import os
from typing import Dict, List, Optional

import joblib
import numpy as np
import pandas as pd
from django.conf import settings
from django.utils import timezone

from houses.models import House, HouseFeatureSnapshot
from rotem_scraper.models import MLModel, MLPrediction, RotemController

logger = logging.getLogger(__name__)

FEATURE_FIELDS = [
    'avg_temp',
    'humidity',
    'static_pressure',
    'vent_level',
    'outside_temp',
    'water_24h',
    'feed_24h',
    'water_delta_1h',
    'temp_std_6h',
    'heater_runtime_24h',
]


class MLMultivariateService:
    """Train and score per-farm multivariate isolation forest models."""

    MODEL_NAME = 'multivariate_anomaly'

    def __init__(self):
        self.models_dir = getattr(
            settings, 'ML_MODELS_DIR', os.path.join(settings.BASE_DIR, 'ml_models')
        )
        os.makedirs(self.models_dir, exist_ok=True)

    def _path(self, farm_id: int) -> str:
        return os.path.join(self.models_dir, f'multivariate_farm_{farm_id}.joblib')

    def train_farm(self, farm_id: int, days: int = 30) -> bool:
        from datetime import timedelta
        from farms.models import Farm

        try:
            farm = Farm.objects.get(id=farm_id)
        except Farm.DoesNotExist:
            return False

        since = timezone.now() - timedelta(days=days)
        house_ids = list(farm.houses.filter(is_active=True).values_list('id', flat=True))
        if not house_ids:
            return False

        rows = HouseFeatureSnapshot.objects.filter(
            house_id__in=house_ids,
            timestamp__gte=since,
        ).values(*FEATURE_FIELDS)
        df = pd.DataFrame(list(rows)).dropna(how='all')
        if len(df) < 100:
            logger.warning("Farm %s: insufficient feature rows (%s) for multivariate training", farm_id, len(df))
            return False

        X = df[FEATURE_FIELDS].fillna(df[FEATURE_FIELDS].median()).values
        from sklearn.ensemble import IsolationForest
        from sklearn.preprocessing import StandardScaler

        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        model = IsolationForest(contamination=0.08, random_state=42, n_estimators=120)
        model.fit(X_scaled)

        joblib.dump(
            {'model': model, 'scaler': scaler, 'features': FEATURE_FIELDS},
            self._path(farm_id),
        )
        MLModel.objects.update_or_create(
            name=f'{self.MODEL_NAME}_farm_{farm_id}',
            defaults={
                'version': '1.0',
                'model_type': 'isolation_forest_multivariate',
                'is_active': True,
                'training_data_size': len(df),
                'last_trained': timezone.now(),
                'model_file_path': self._path(farm_id),
            },
        )
        return True

    def score_farm(self, farm_id: int) -> List[MLPrediction]:
        path = self._path(farm_id)
        if not os.path.exists(path):
            return []

        bundle = joblib.load(path)
        model = bundle['model']
        scaler = bundle['scaler']
        features = bundle['features']

        from farms.models import Farm

        try:
            farm = Farm.objects.get(id=farm_id)
        except Farm.DoesNotExist:
            return []

        controller = farm.rotem_controllers.filter(is_connected=True).first()
        if not controller:
            return []

        predictions: List[MLPrediction] = []
        for house in farm.houses.filter(is_active=True):
            snap = (
                HouseFeatureSnapshot.objects.filter(house=house)
                .order_by('-timestamp')
                .first()
            )
            if not snap:
                continue
            row = [getattr(snap, f, 0) or 0 for f in features]
            X = scaler.transform([row])
            label = model.predict(X)[0]
            score = float(model.score_samples(X)[0])
            if label != -1:
                continue

            pred = MLPrediction.objects.create(
                controller=controller,
                prediction_type='anomaly',
                predicted_at=timezone.now(),
                confidence_score=min(1.0, abs(score)),
                prediction_data={
                    'analysis_type': 'multivariate',
                    'house_id': house.id,
                    'house_number': house.house_number,
                    'farm_id': farm_id,
                    'anomaly_score': score,
                    'features': {f: getattr(snap, f) for f in features},
                    'severity': 'high' if abs(score) > 0.5 else 'medium',
                },
            )
            predictions.append(pred)
        return predictions

    def train_all_farms(self) -> Dict:
        from farms.models import Farm

        results = {'trained': 0, 'skipped': 0}
        for farm in Farm.objects.filter(has_system_integration=True, integration_type='rotem'):
            if self.train_farm(farm.id):
                results['trained'] += 1
            else:
                results['skipped'] += 1
        return results

    def score_all_farms(self) -> List[MLPrediction]:
        from farms.models import Farm

        all_preds: List[MLPrediction] = []
        for farm in Farm.objects.filter(has_system_integration=True, integration_type='rotem'):
            all_preds.extend(self.score_farm(farm.id))
        return all_preds
