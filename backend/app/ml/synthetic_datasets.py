"""
Training and synthetic dataset generator for Agricultural AI models.
Generates realistic crop suitability and yield regression training datasets
grounded in agronomic principles (ICAR & FAO guidelines).
"""

import numpy as np
import pandas as pd
from typing import Tuple
from backend.app.data.crop_database import CROPS_DATABASE


def generate_crop_suitability_dataset(samples_per_crop: int = 150, seed: int = 42) -> pd.DataFrame:
    """
    Generates synthetic agronomic dataset for crop classification matching ICAR benchmarks.
    Features: N, P, K, temperature, humidity, ph, rainfall
    Target: crop_id
    """
    rng = np.random.default_rng(seed)
    records = []

    for crop_id, crop in CROPS_DATABASE.items():
        for _ in range(samples_per_crop):
            # N, P, K centered on crop ideals with natural soil variability (std dev ~ 15-20%)
            n = max(5.0, rng.normal(crop.ideal_n, crop.ideal_n * 0.18))
            p = max(5.0, rng.normal(crop.ideal_p, crop.ideal_p * 0.18))
            k = max(5.0, rng.normal(crop.ideal_k, crop.ideal_k * 0.18))

            # pH within tolerance band
            ph_mid = (crop.ideal_ph_min + crop.ideal_ph_max) / 2.0
            ph_span = (crop.ideal_ph_max - crop.ideal_ph_min) / 2.0
            ph = np.clip(rng.normal(ph_mid, ph_span * 0.5), 4.0, 9.5)

            # Temp within crop threshold
            t_mid = (crop.ideal_temp_min + crop.ideal_temp_max) / 2.0
            t_span = (crop.ideal_temp_max - crop.ideal_temp_min) / 2.0
            temp = rng.normal(t_mid, t_span * 0.45)

            # Humidity
            h_mid = (crop.ideal_humidity_min + crop.ideal_humidity_max) / 2.0
            h_span = (crop.ideal_humidity_max - crop.ideal_humidity_min) / 2.0
            hum = np.clip(rng.normal(h_mid, h_span * 0.45), 15.0, 99.0)

            # Rainfall
            r_mid = (crop.ideal_rainfall_min + crop.ideal_rainfall_max) / 2.0
            r_span = (crop.ideal_rainfall_max - crop.ideal_rainfall_min) / 2.0
            rain = max(50.0, rng.normal(r_mid, r_span * 0.45))

            records.append({
                "N": round(float(n), 1),
                "P": round(float(p), 1),
                "K": round(float(k), 1),
                "temperature": round(float(temp), 2),
                "humidity": round(float(hum), 2),
                "ph": round(float(ph), 2),
                "rainfall": round(float(rain), 1),
                "label": crop_id
            })

    return pd.DataFrame(records)


def generate_yield_dataset(samples_per_crop: int = 150, seed: int = 42) -> pd.DataFrame:
    """
    Generates synthetic dataset for yield regression (quintals per acre).
    Features: crop_id, N, P, K, ph, temperature, rainfall, water_available_kl, fertilizer_applied_kg
    Target: yield_q_per_acre
    """
    rng = np.random.default_rng(seed)
    records = []

    for crop_id, crop in CROPS_DATABASE.items():
        for _ in range(samples_per_crop):
            n = max(5.0, rng.normal(crop.ideal_n, crop.ideal_n * 0.25))
            p = max(5.0, rng.normal(crop.ideal_p, crop.ideal_p * 0.25))
            k = max(5.0, rng.normal(crop.ideal_k, crop.ideal_k * 0.25))

            ph_mid = (crop.ideal_ph_min + crop.ideal_ph_max) / 2.0
            ph = np.clip(rng.normal(ph_mid, 0.6), 4.5, 9.0)

            t_mid = (crop.ideal_temp_min + crop.ideal_temp_max) / 2.0
            temp = rng.normal(t_mid, 3.5)

            r_mid = (crop.ideal_rainfall_min + crop.ideal_rainfall_max) / 2.0
            rain = max(50.0, rng.normal(r_mid, r_mid * 0.25))

            water_ratio = rng.uniform(0.65, 1.25)
            water_avail = crop.water_requirement_kl * water_ratio

            fert_ratio = rng.uniform(0.65, 1.30)
            fert_applied = crop.total_fertilizer_kg * fert_ratio

            # Agronomic Liebig's Law of the Minimum / Mitscherlich response curve
            n_factor = min(1.15, n / max(1.0, crop.ideal_n))
            p_factor = min(1.15, p / max(1.0, crop.ideal_p))
            k_factor = min(1.15, k / max(1.0, crop.ideal_k))
            nutrient_factor = (n_factor * 0.45 + p_factor * 0.30 + k_factor * 0.25)

            ph_penalty = 1.0 - 0.25 * (abs(ph - ph_mid) / max(0.5, ph_mid - crop.ideal_ph_min))
            ph_penalty = np.clip(ph_penalty, 0.60, 1.0)

            water_response = min(1.05, (water_avail / crop.water_requirement_kl) ** 0.5)

            # Expected yield calculation
            base = crop.base_yield_quintals_per_acre
            actual_yield = base * nutrient_factor * ph_penalty * water_response * rng.normal(1.0, 0.05)
            actual_yield = max(base * 0.35, actual_yield)

            records.append({
                "crop_id": crop_id,
                "N": round(float(n), 1),
                "P": round(float(p), 1),
                "K": round(float(k), 1),
                "ph": round(float(ph), 2),
                "temperature": round(float(temp), 2),
                "rainfall": round(float(rain), 1),
                "water_available_kl": round(float(water_avail), 1),
                "fertilizer_applied_kg": round(float(fert_applied), 1),
                "yield_q_per_acre": round(float(actual_yield), 2)
            })

    return pd.DataFrame(records)
