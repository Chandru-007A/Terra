"""
Tests for Agricultural Dataset Acquisition, Audit, Provenance, and Real-Data Evaluation.

Phase 4 Audit Coverage:
1. Origin Verification: Confirms dataset sources, authors, and licenses (Atharva Ingle / Kaggle for crop recommendation; DES India for district production).
2. Reproduction of 99.64% Classifier CV Score: Tests zero duplicates, measures cluster separability, and verifies methodology disclaimers.
3. Audit of 122,427 Yield Records: Verifies raw counts (246,091), matching Terra crops (125,827), dropped NaNs (1,297), dropped zero-production (562), ICAR outliers (1,535), retained clean records (122,427), unit conversions, and coverage.
4. Yield Percentiles Verification: Tests exact percentile rank of base yields against empirical district records (e.g. Cotton ~69.4%, Wheat ~96.6%, Rice ~99.9%, Onion ~89.9%, Sugarcane ~85.2%).
5. Separation of Concerns: Asserts regional historical macro-benchmarking is strictly decoupled from farm-level predictive validation (preventing ecological fallacy).
6. FastAPI /data API Endpoints: Verifies /data/provenance, /data/benchmarks/{crop_id}, /data/climate/{district_id}, /data/evaluation/classifier, /data/evaluation/regressor.
"""

import os
import json
from pathlib import Path
import pytest
import pandas as pd
import numpy as np
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.data.real_data_pipeline import pipeline
from backend.app.data.crop_database import CROPS_DATABASE
from backend.app.data.process_datasets import CROP_NAME_MAPPING, ICAR_PHYSIOLOGICAL_YIELD_BOUNDS

client = TestClient(app)

REPO_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = REPO_ROOT / "data" / "raw"
PROCESSED_DIR = REPO_ROOT / "data" / "processed"


# ─── 1. Raw Dataset Integrity & Source Verification ──────────────────────────

class TestRawDatasetsAndSources:
    """Verifies that original downloaded public datasets exist and are intact."""

    def test_raw_district_crop_production_exists(self):
        csv_path = RAW_DIR / "crop_production_india.csv"
        assert csv_path.exists(), f"Missing raw file: {csv_path}"
        assert csv_path.stat().st_size > 15_000_000, "Raw crop production CSV should be > 15MB"

    def test_raw_crop_recommendation_exists(self):
        csv_path = RAW_DIR / "crop_recommendation.csv"
        assert csv_path.exists(), f"Missing raw file: {csv_path}"
        assert csv_path.stat().st_size > 100_000, "Raw crop recommendation CSV should be > 100KB"

    def test_raw_nasa_power_climatology_exists(self):
        json_path = RAW_DIR / "nasa_power_climatology_districts.json"
        assert json_path.exists(), f"Missing raw file: {json_path}"
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert len(data) >= 8, "Expected at least 8 districts in raw climatology"

    def test_raw_nasa_power_monthly_exists(self):
        json_path = RAW_DIR / "nasa_power_monthly_2010_2015.json"
        assert json_path.exists(), f"Missing raw file: {json_path}"
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert len(data) >= 4, "Expected monthly historical data for key districts"


# ─── 2. Audit of the 2,200-Row Crop Recommendation Benchmark ─────────────────

class TestCropRecommendationAudit:
    """
    Audits the 2,200-row crop recommendation dataset:
    - Author: Atharva Ingle (Kaggle)
    - Nature: Synthetically augmented precision agriculture benchmark (NOT uncurated ICAR IoT telemetry)
    - Reproduces the 99.64% CV score and explains its scope and limitations.
    """

    def test_author_and_nature_in_provenance(self):
        catalog = pipeline.load_provenance_catalog()
        rec_meta = catalog["datasets"]["crop_suitability_real"]
        assert "Atharva Ingle" in rec_meta["author"]
        assert "atharvaingle/crop-recommendation-dataset" in rec_meta["source_url"]
        assert rec_meta["data_nature"].startswith("AUGMENTED")
        assert "NOT raw uncurated ICAR" in rec_meta["data_nature"]

    def test_no_exact_duplicates_in_benchmark(self):
        df = pipeline.load_real_crop_suitability_dataset()
        features = ["N", "P", "K", "temperature", "humidity", "ph", "rainfall"]
        assert df.duplicated().sum() == 0, "No duplicate rows should exist"
        assert df.duplicated(subset=features).sum() == 0, "No duplicate feature vectors should exist"

    def test_balanced_classes_100_samples_each(self):
        df = pipeline.load_real_crop_suitability_dataset()
        counts = df["label_raw"].value_counts()
        assert len(counts) == 22, "Expected 22 crop classes"
        assert (counts == 100).all(), "Every crop must have exactly 100 observations"

    def test_reproduce_99_percent_cv_score(self):
        """
        Reproduces the reported ~99.64% cross-validation score.
        Confirms that the evaluation reports its methodological scope.
        """
        report = pipeline.evaluate_classifier_on_real_data(n_folds=5)
        assert report["cv_accuracy_mean"] >= 0.98, "CV accuracy should be ~99%"
        assert report["evaluated_on"] == "ATHARVA_INGLE_KAGGLE_BENCHMARK"
        assert report["is_raw_field_telemetry"] is False
        assert "cluster separability" in report["methodological_scope"]


# ─── 3. Forensic Audit of 122,427 District Crop Yield Records ─────────────────

class TestDistrictYieldAudit:
    """
    Forensic raw-to-clean accounting of official Indian district-wise crop production data:
    Raw rows -> Terra crop filter -> Null exclusions -> Outlier exclusions -> Clean records.
    """

    def test_raw_to_clean_filtering_counts(self):
        raw_path = RAW_DIR / "crop_production_india.csv"
        raw = pd.read_csv(raw_path)
        raw.columns = [c.strip() for c in raw.columns]
        raw["Crop_Raw"] = raw["Crop"].str.strip()

        # Step 1: Raw count
        assert len(raw) == 246_091, f"Expected 246,091 raw rows, got {len(raw)}"

        # Step 2: Terra 20 crops match
        terra_mask = raw["Crop_Raw"].isin(CROP_NAME_MAPPING.keys())
        assert terra_mask.sum() == 125_827, f"Expected 125,827 Terra rows, got {terra_mask.sum()}"

        df_terra = raw[terra_mask].copy()
        df_terra["crop_id"] = df_terra["Crop_Raw"].map(CROP_NAME_MAPPING)

        # Step 3: Dropped NaNs in Terra crops
        nan_prod = df_terra["Production"].isna().sum()
        assert nan_prod == 1_297, f"Expected 1,297 NaN production rows in Terra crops, got {nan_prod}"

        # Step 4: Dropped zero-production in Terra crops
        zero_prod = ((df_terra["Production"] == 0) & df_terra["Production"].notna()).sum()
        assert zero_prod == 562, f"Expected 562 zero-production rows, got {zero_prod}"

        # Step 5: Valid positive production and Area >= 1.0 ha
        valid_mask = df_terra["Production"].notna() & (df_terra["Area"] >= 1.0) & (df_terra["Production"] > 0)
        assert valid_mask.sum() == 123_962, f"Expected 123,962 pre-outlier rows, got {valid_mask.sum()}"

        # Step 6: Processed file count exactly equals 122,427
        processed = pipeline.load_district_yield_dataset()
        assert len(processed) == 122_427, f"Expected 122,427 processed records, got {len(processed)}"

    def test_coverage_states_districts_and_years(self):
        df = pipeline.load_district_yield_dataset()
        assert df["district"].nunique() == 646, f"Expected 646 districts, got {df['district'].nunique()}"
        assert df["state"].nunique() == 33, f"Expected 33 states/UTs, got {df['state'].nunique()}"
        assert df["crop_year"].min() == 1997
        assert df["crop_year"].max() == 2015

    def test_watermelon_gap_honestly_documented(self):
        """
        Verifies that in raw data, Water Melon only exists with 0.0 production (85 rows).
        Confirms zero fabrication: watermelon has 0 valid district yield records.
        """
        raw_path = RAW_DIR / "crop_production_india.csv"
        raw = pd.read_csv(raw_path)
        wm = raw[raw["Crop"].str.strip() == "Water Melon"]
        assert len(wm) == 85
        assert (wm["Production"] == 0.0).all()

        processed = pipeline.load_district_yield_dataset()
        wm_clean = processed[processed["crop_id"] == "watermelon"]
        assert len(wm_clean) == 0, "Watermelon with 0.0 production must NOT be included in yield data"

    def test_unit_conversion_math(self):
        df = pipeline.load_district_yield_dataset().head(50)
        # 1 ha = 2.47105 acres
        area_diff = (df["area_acres"] - df["area_ha"] * 2.47105).abs()
        assert (area_diff < 0.05).all()

        # 1 tonne = 10 quintals
        prod_diff = (df["production_quintals"] - df["production_tonnes"] * 10.0).abs()
        assert (prod_diff < 0.05).all()

        # Yield = production_quintals / area_acres
        expected_yield = np.round(df["production_quintals"] / df["area_acres"], 2)
        yield_diff = (df["yield_q_per_acre"] - expected_yield).abs()
        assert (yield_diff < 0.05).all()


# ─── 4. Verification of Yield-Percentile Calculations ─────────────────────────

class TestYieldPercentilesVerification:
    """Verifies that model base yields align with source-supported empirical percentiles."""

    def test_cotton_percentile_around_70(self):
        bench = pipeline.benchmark_regressor_against_real_yields()["benchmarks"]["cotton"]
        # Cotton base yield 8.0 q/acre is at ~69.4% of district statistics
        assert 68.0 <= bench["percentile_of_base_yield"] <= 71.0

    def test_wheat_percentile_around_96(self):
        bench = pipeline.benchmark_regressor_against_real_yields()["benchmarks"]["wheat"]
        # Wheat base yield 18.0 q/acre is at ~96.6% of district statistics
        assert 95.0 <= bench["percentile_of_base_yield"] <= 98.0

    def test_rice_percentile_around_99(self):
        bench = pipeline.benchmark_regressor_against_real_yields()["benchmarks"]["rice"]
        # Rice base yield 22.0 q/acre is at ~99.9% of district statistics
        assert 99.0 <= bench["percentile_of_base_yield"] <= 100.0

    def test_onion_percentile_around_90(self):
        bench = pipeline.benchmark_regressor_against_real_yields()["benchmarks"]["onion"]
        # Onion base yield 90.0 q/acre is at ~89.9% of district statistics
        assert 88.0 <= bench["percentile_of_base_yield"] <= 91.0

    def test_sugarcane_percentile_around_85(self):
        bench = pipeline.benchmark_regressor_against_real_yields()["benchmarks"]["sugarcane"]
        # Sugarcane base yield 350.0 q/acre is at ~85.2% of district statistics
        assert 84.0 <= bench["percentile_of_base_yield"] <= 87.0


# ─── 5. Separation of Regional Benchmarking from Farm Predictive Validation ───

class TestDecouplingRegionalFromFarmLevel:
    """
    Verifies that regional macro-benchmarking is strictly distinguished
    from farm-level predictive validation to avoid the ecological fallacy.
    """

    def test_regressor_benchmark_declares_predictive_limitation(self):
        report = pipeline.benchmark_regressor_against_real_yields()
        assert report["evaluation_type"] == "REGIONAL_HISTORICAL_BENCHMARKING"
        assert "NOT VALIDATED AT FARM LEVEL" in report["predictive_validation_status"]
        assert "ecological fallacy" in report["predictive_validation_status"].lower()

    def test_provenance_catalog_declares_ecological_fallacy(self):
        catalog = pipeline.load_provenance_catalog()
        adequacy = catalog["datasets"]["official_crop_production_india"]["adequacy_for_ml_evaluation"]
        assert "CANNOT VALIDATE FARM-LEVEL" in adequacy["farm_level_predictive_limitation"]
        assert "ecological fallacy" in adequacy["farm_level_predictive_limitation"].lower()


# ─── 6. FastAPI Endpoints (/data) Verification ───────────────────────────────

class TestDataAPIEndpoints:
    """Verifies that all /data endpoints return accurate schemas and proper HTTP status codes."""

    def test_get_provenance_endpoint(self):
        r = client.get("/data/provenance")
        assert r.status_code == 200
        data = r.json()
        assert "datasets" in data
        assert "official_crop_production_india" in data["datasets"]
        assert "crop_suitability_real" in data["datasets"]

    def test_get_benchmarks_valid_crop(self):
        r = client.get("/data/benchmarks/wheat?season=Rabi")
        assert r.status_code == 200
        data = r.json()
        assert data["crop_id"] == "wheat"
        assert data["observation_count"] == 7490
        assert data["median"] == 7.91

    def test_get_benchmarks_unknown_crop_returns_404(self):
        r = client.get("/data/benchmarks/dragonfruit")
        assert r.status_code == 404

    def test_get_district_climate_valid(self):
        r = client.get("/data/climate/nashik_maharashtra")
        assert r.status_code == 200
        data = r.json()
        assert data["district_id"] == "nashik_maharashtra"
        assert data["annual"]["temperature_c"] == 24.43

    def test_get_district_climate_unknown_returns_404(self):
        r = client.get("/data/climate/atlantis_city")
        assert r.status_code == 404

    def test_get_classifier_real_evaluation_endpoint(self):
        r = client.get("/data/evaluation/classifier?n_folds=3")
        assert r.status_code == 200
        data = r.json()
        assert data["cv_accuracy_mean"] >= 0.98
        assert data["evaluated_on"] == "ATHARVA_INGLE_KAGGLE_BENCHMARK"
        assert data["is_raw_field_telemetry"] is False

    def test_get_regressor_real_benchmarks_endpoint(self):
        r = client.get("/data/evaluation/regressor")
        assert r.status_code == 200
        data = r.json()
        assert data["total_crops_evaluated"] == 19
        assert data["evaluation_type"] == "REGIONAL_HISTORICAL_BENCHMARKING"
        assert "NOT VALIDATED AT FARM LEVEL" in data["predictive_validation_status"]
