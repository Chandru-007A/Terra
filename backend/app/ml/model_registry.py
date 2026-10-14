"""
Central Model Registry and Lifecycle Manager for TERRA ML Services.
Ensures lightweight singleton initialization and model persistence.
"""

import os
import joblib
from typing import Optional
from backend.app.ml.crop_classifier import CropSuitabilityClassifier
from backend.app.ml.yield_regressor import YieldPredictionRegressor

CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "models_cache")


class ModelRegistry:
    _instance: Optional["ModelRegistry"] = None

    def __init__(self):
        self.crop_classifier: Optional[CropSuitabilityClassifier] = None
        self.yield_regressor: Optional[YieldPredictionRegressor] = None
        os.makedirs(CACHE_DIR, exist_ok=True)

    @classmethod
    def get_instance(cls) -> "ModelRegistry":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def get_crop_classifier(self) -> CropSuitabilityClassifier:
        if self.crop_classifier is None:
            cache_path = os.path.join(CACHE_DIR, "crop_classifier.joblib")
            if os.path.exists(cache_path):
                try:
                    self.crop_classifier = joblib.load(cache_path)
                except Exception:
                    self.crop_classifier = CropSuitabilityClassifier()
                    self.crop_classifier.train()
                    joblib.dump(self.crop_classifier, cache_path)
            else:
                self.crop_classifier = CropSuitabilityClassifier()
                self.crop_classifier.train()
                try:
                    joblib.dump(self.crop_classifier, cache_path)
                except Exception:
                    pass
        return self.crop_classifier

    def get_yield_regressor(self) -> YieldPredictionRegressor:
        if self.yield_regressor is None:
            cache_path = os.path.join(CACHE_DIR, "yield_regressor.joblib")
            if os.path.exists(cache_path):
                try:
                    self.yield_regressor = joblib.load(cache_path)
                except Exception:
                    self.yield_regressor = YieldPredictionRegressor()
                    self.yield_regressor.train()
                    joblib.dump(self.yield_regressor, cache_path)
            else:
                self.yield_regressor = YieldPredictionRegressor()
                self.yield_regressor.train()
                try:
                    joblib.dump(self.yield_regressor, cache_path)
                except Exception:
                    pass
        return self.yield_regressor


registry = ModelRegistry.get_instance()
