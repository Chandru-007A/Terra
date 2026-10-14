"""
Crop Yield Prediction Regressor using Gradient Boosting.
Predicts expected harvest yield (quintals/acre) and a heuristic prediction range
based on soil nutrients, climatic conditions, and resource inputs.

IMPORTANT — DATA LIMITATION: This model is trained entirely on SYNTHETIC data
generated from agronomic principles (see synthetic_datasets.py). It has NOT been
validated on real held-out farm data. Yield predictions are indicative only and
should not be used to make financial decisions without local agronomic validation.
The ±10% prediction range is a heuristic estimate, NOT a statistically validated
95% confidence interval.
"""

from typing import Dict, Any, Optional, List
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import KFold
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from backend.app.data.crop_database import CROPS_DATABASE, get_crop
from backend.app.ml.synthetic_datasets import generate_yield_dataset


class YieldPredictionRegressor:
    def __init__(self):
        self.models: Dict[str, GradientBoostingRegressor] = {}
        self._is_trained: bool = False
        self._evaluation_report: Optional[Dict[str, Any]] = None

    def train(self, dataset: Optional[Any] = None) -> None:
        """Trains dedicated gradient boosting regressors for each crop on synthetic data."""
        if dataset is None:
            dataset = generate_yield_dataset(samples_per_crop=150, seed=42)

        feature_cols = [
            "N", "P", "K", "ph", "temperature", "rainfall",
            "water_available_kl", "fertilizer_applied_kg"
        ]

        for crop_id in CROPS_DATABASE.keys():
            crop_df = dataset[dataset["crop_id"] == crop_id]
            if len(crop_df) < 10:
                continue

            X = crop_df[feature_cols].values
            y = crop_df["yield_q_per_acre"].values

            model = GradientBoostingRegressor(
                n_estimators=80,
                learning_rate=0.08,
                max_depth=4,
                random_state=42
            )
            model.fit(X, y)
            self.models[crop_id] = model

        self._is_trained = True

    def evaluate(self, dataset: Optional[Any] = None, n_folds: int = 5) -> Dict[str, Any]:
        """
        Evaluates yield prediction quality via k-fold cross-validation on the training dataset.

        DATA LIMITATION: All evaluation is on SYNTHETIC data generated from agronomic
        principles. CV scores measure internal consistency of the synthetic model, NOT
        real-world prediction accuracy. Do not cite these metrics as validated accuracy
        on real farm data.

        Leakage prevention: Folds are split per-crop on independent samples.
        No temporal leakage possible since synthetic data has no time component.
        """
        if dataset is None:
            dataset = generate_yield_dataset(samples_per_crop=150, seed=42)

        feature_cols = [
            "N", "P", "K", "ph", "temperature", "rainfall",
            "water_available_kl", "fertilizer_applied_kg"
        ]

        all_rmse: List[float] = []
        all_mae: List[float] = []
        all_r2: List[float] = []
        crop_metrics: Dict[str, Any] = {}

        kf = KFold(n_splits=n_folds, shuffle=True, random_state=42)

        for crop_id in CROPS_DATABASE.keys():
            crop_df = dataset[dataset["crop_id"] == crop_id].reset_index(drop=True)
            if len(crop_df) < n_folds * 2:
                continue

            X = crop_df[feature_cols].values
            y = crop_df["yield_q_per_acre"].values

            fold_rmse, fold_mae, fold_r2 = [], [], []
            for train_idx, test_idx in kf.split(X):
                m = GradientBoostingRegressor(
                    n_estimators=80, learning_rate=0.08,
                    max_depth=4, random_state=42
                )
                m.fit(X[train_idx], y[train_idx])
                preds = m.predict(X[test_idx])
                fold_rmse.append(float(np.sqrt(mean_squared_error(y[test_idx], preds))))
                fold_mae.append(float(mean_absolute_error(y[test_idx], preds)))
                fold_r2.append(float(r2_score(y[test_idx], preds)))

            cv_rmse = float(np.mean(fold_rmse))
            cv_mae  = float(np.mean(fold_mae))
            cv_r2   = float(np.mean(fold_r2))
            crop_metrics[crop_id] = {
                "n_samples": len(crop_df),
                "cv_rmse_q_per_acre": round(cv_rmse, 3),
                "cv_mae_q_per_acre":  round(cv_mae, 3),
                "cv_r2": round(cv_r2, 3),
            }
            all_rmse.append(cv_rmse)
            all_mae.append(cv_mae)
            all_r2.append(cv_r2)

        report = {
            "model": "GradientBoostingRegressor (per-crop)",
            "n_folds": n_folds,
            "total_samples": len(dataset),
            "crops_evaluated": len(crop_metrics),
            "aggregate": {
                "mean_cv_rmse_q_per_acre": round(float(np.mean(all_rmse)), 3) if all_rmse else None,
                "mean_cv_mae_q_per_acre":  round(float(np.mean(all_mae)),  3) if all_mae else None,
                "mean_cv_r2":              round(float(np.mean(all_r2)),   3) if all_r2 else None,
            },
            "per_crop": crop_metrics,
            "data_source": "SYNTHETIC — generated from ICAR/FAO agronomic principles",
            "limitations": (
                "CV scores reflect internal fit quality on synthetic data only. "
                "These are NOT validated accuracy metrics on real farm records. "
                "High R² on synthetic data is expected since features were generated "
                "from the same agronomic model used to produce labels. "
                "Do not cite as prediction accuracy without real-data validation."
            ),
            "leakage_note": (
                f"{n_folds}-fold CV with shuffle; no time-based leakage (synthetic data). "
                "Folds are independent per-crop subsets."
            ),
        }
        self._evaluation_report = report
        return report

    def get_model_info(self) -> Dict[str, Any]:
        """Returns lightweight model metadata without running evaluation."""
        eval_report = getattr(self, '_evaluation_report', None)
        return {
            "model_type": "GradientBoostingRegressor (per-crop ensemble)",
            "crops_trained": len(self.models),
            "is_trained": self._is_trained,
            "data_basis": "Synthetic — ICAR/FAO agronomic principles",
            "evaluation_available": eval_report is not None,
            "disclaimer": (
                "Trained on synthetic data. Not validated against real farm records. "
                "Results are indicative only."
            ),
        }


    def predict_yield(
        self,
        crop_id: str,
        n: float,
        p: float,
        k: float,
        ph: float,
        temperature: float,
        rainfall: float,
        water_available_kl: Optional[float] = None,
        fertilizer_applied_kg: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Predicts expected yield (q/acre) for a specific crop under given soil/weather conditions.
        Trained on synthetic data; results are indicative, not validated against real farm records.
        """
        crop = get_crop(crop_id)
        if not crop:
            raise ValueError(f"Unknown crop ID: {crop_id}")

        if not self._is_trained:
            self.train()

        # Defaults if resource inputs not specified
        if water_available_kl is None:
            water_available_kl = crop.water_requirement_kl
        if fertilizer_applied_kg is None:
            fertilizer_applied_kg = crop.total_fertilizer_kg

        model = self.models.get(crop.id)
        if model is not None:
            features = np.array([[
                n, p, k, ph, temperature, rainfall,
                water_available_kl, fertilizer_applied_kg
            ]])
            predicted_raw = float(model.predict(features)[0])
        else:
            predicted_raw = crop.base_yield_quintals_per_acre

        # Guardrails: yield should be realistic for the crop
        min_feasible = crop.base_yield_quintals_per_acre * 0.40
        max_feasible = crop.base_yield_quintals_per_acre * 1.35
        expected_yield = round(float(np.clip(predicted_raw, min_feasible, max_feasible)), 2)

        # Heuristic prediction range (+/- 10%).
        # NOTE: This is NOT a statistically validated 95% confidence interval.
        # It is a rough heuristic band reflecting typical agronomic variability on
        # synthetic training data. Do not interpret as a formal statistical guarantee.
        pred_lower = round(expected_yield * 0.90, 2)
        pred_upper = round(expected_yield * 1.10, 2)

        # Revenue and Profit calculations
        gross_revenue = round(expected_yield * crop.market_price_per_quintal, 2)
        net_profit = round(gross_revenue - crop.cultivation_cost_per_acre, 2)
        margin = round((net_profit / gross_revenue) * 100, 1) if gross_revenue > 0 else 0.0

        # Yield gap vs standard benchmark
        yield_gap_percent = round(
            ((expected_yield - crop.base_yield_quintals_per_acre) / crop.base_yield_quintals_per_acre) * 100, 1
        )

        return {
            "crop_id": crop.id,
            "crop_name": crop.name,
            "emoji": crop.emoji,
            "expected_yield_q_per_acre": expected_yield,
            # Named to clarify these are heuristic bounds, not a validated 95% CI
            "confidence_interval_95": {
                "lower_q_per_acre": pred_lower,
                "upper_q_per_acre": pred_upper,
            },
            "prediction_range_note": (
                "Range is a ±10% heuristic estimate (synthetic-data model). "
                "Not a statistically validated 95% confidence interval."
            ),
            "benchmark_yield_q_per_acre": crop.base_yield_quintals_per_acre,
            "yield_gap_percent": yield_gap_percent,
            "market_price_per_q": crop.market_price_per_quintal,
            "gross_revenue_per_acre": gross_revenue,
            "cultivation_cost_per_acre": crop.cultivation_cost_per_acre,
            "expected_profit_per_acre": net_profit,
            "profit_margin_percent": margin,
            "water_required_kl_per_acre": crop.water_requirement_kl,
            "fertilizer_required_kg_per_acre": crop.total_fertilizer_kg,
        }

