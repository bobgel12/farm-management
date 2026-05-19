"""Supervised mortality / FCR risk scoring from flock performance history."""
from __future__ import annotations

import logging
import os
from typing import Dict, List, Optional

import joblib
import numpy as np
import pandas as pd
from django.conf import settings
from django.db.models import Max
from sklearn.ensemble import GradientBoostingClassifier, GradientBoostingRegressor
from sklearn.model_selection import cross_val_score
from sklearn.preprocessing import StandardScaler

from farms.models import Flock, FlockPerformance
from houses.models import FlockRiskScore

logger = logging.getLogger(__name__)

FEATURE_COLUMNS = [
    'flock_age_days',
    'average_temperature',
    'average_humidity',
    'daily_water_consumption_liters',
    'daily_feed_consumption_kg',
    'mortality_rate',
    'livability',
    'feed_conversion_ratio',
]


class MortalityRiskService:
    MODEL_VERSION = 'mortality_risk_v1'

    def __init__(self):
        self.models_dir = getattr(
            settings, 'ML_MODELS_DIR', os.path.join(settings.BASE_DIR, 'ml_models')
        )
        os.makedirs(self.models_dir, exist_ok=True)

    def _model_path(self, name: str) -> str:
        return os.path.join(self.models_dir, name)

    def build_training_frame(self, min_flocks: int = 3) -> Optional[pd.DataFrame]:
        rows: List[Dict] = []
        flocks = Flock.objects.filter(
            status__in=['growing', 'production', 'completed']
        ).select_related('house')
        for flock in flocks:
            for perf in FlockPerformance.objects.filter(flock=flock).order_by('flock_age_days'):
                row = {col: getattr(perf, col, None) for col in FEATURE_COLUMNS}
                row['flock_id'] = flock.id
                row['house_id'] = flock.house_id
                future = FlockPerformance.objects.filter(
                    flock=flock,
                    flock_age_days__gt=perf.flock_age_days,
                    flock_age_days__lte=perf.flock_age_days + 3,
                ).aggregate(max_mort=Max('mortality_rate'))
                max_future_mort = future.get('max_mort') or 0
                current_mort = perf.mortality_rate or 0
                row['mortality_spike_3d'] = (
                    1 if max_future_mort > max(0.5, current_mort * 1.5) else 0
                )
                rows.append(row)

        if len(rows) < 30:
            return None
        df = pd.DataFrame(rows)
        if df['flock_id'].nunique() < min_flocks:
            return None
        return df

    def train_mortality_classifier(self) -> bool:
        df = self.build_training_frame()
        if df is None or df.empty:
            logger.warning("Insufficient labeled data for mortality model training")
            return False

        X = df[FEATURE_COLUMNS].fillna(0).values
        y = df['mortality_spike_3d'].values
        if len(np.unique(y)) < 2:
            logger.warning("Mortality labels lack both classes; skipping training")
            return False

        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        model = GradientBoostingClassifier(
            n_estimators=100,
            max_depth=4,
            learning_rate=0.08,
            random_state=42,
        )
        try:
            cv = min(3, len(np.unique(y)))
            scores = cross_val_score(model, X_scaled, y, cv=cv, scoring='roc_auc')
            auc = float(np.mean(scores))
        except Exception:
            auc = None

        model.fit(X_scaled, y)
        joblib.dump(
            {'model': model, 'scaler': scaler, 'features': FEATURE_COLUMNS, 'auc': auc},
            self._model_path('mortality_risk_v1.joblib'),
        )
        logger.info("Trained mortality_risk_v1 samples=%s auc=%s", len(df), auc)
        return True

    def score_active_flocks(self) -> List[FlockRiskScore]:
        path = self._model_path('mortality_risk_v1.joblib')
        if not os.path.exists(path):
            return []

        bundle = joblib.load(path)
        model = bundle['model']
        scaler = bundle['scaler']
        features = bundle['features']
        created: List[FlockRiskScore] = []

        for flock in Flock.objects.filter(is_active=True, status__in=['growing', 'production']):
            perf = (
                FlockPerformance.objects.filter(flock=flock)
                .order_by('-record_date')
                .first()
            )
            if not perf:
                continue
            row = [getattr(perf, col, 0) or 0 for col in features]
            X = scaler.transform([row])
            proba = float(model.predict_proba(X)[0][1])

            score_obj, _ = FlockRiskScore.objects.update_or_create(
                flock=flock,
                risk_type='mortality_3d',
                defaults={
                    'house': flock.house,
                    'score': round(proba, 4),
                    'confidence': 0.7,
                    'model_version': self.MODEL_VERSION,
                    'top_features': {'features_used': features},
                    'flock_age_days': perf.flock_age_days,
                },
            )
            created.append(score_obj)
        return created

    def train_fcr_regressor(self) -> bool:
        rows = []
        for flock in Flock.objects.filter(status='completed'):
            perf = (
                FlockPerformance.objects.filter(flock=flock, flock_age_days__gte=30)
                .order_by('-flock_age_days')
                .first()
            )
            if not perf or perf.feed_conversion_ratio is None:
                continue
            early = FlockPerformance.objects.filter(flock=flock, flock_age_days=14).first()
            if not early:
                continue
            rows.append({
                'early_fcr': early.feed_conversion_ratio or 0,
                'early_water': early.daily_water_consumption_liters or 0,
                'early_mortality': early.mortality_rate or 0,
                'fcr_35': perf.feed_conversion_ratio,
            })
        if len(rows) < 10:
            return False
        df = pd.DataFrame(rows)
        X = df[['early_fcr', 'early_water', 'early_mortality']].values
        y = df['fcr_35'].values
        model = GradientBoostingRegressor(n_estimators=80, max_depth=3, random_state=42)
        model.fit(X, y)
        joblib.dump({'model': model}, self._model_path('fcr_35_v1.joblib'))
        return True
