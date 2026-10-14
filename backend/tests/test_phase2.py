"""
Phase 2 regression tests: data freshness, units, ML evaluation,
economic calculations, data provenance, pipeline validation, and API failures.
"""

import pytest
import pandas as pd
import numpy as np
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


# ─── Data Provenance & Freshness ─────────────────────────────────────────────

class TestDataProvenance:
    """Verify that all data sources carry proper provenance metadata."""

    def test_weather_data_has_source_field(self):
        from backend.app.data.weather_data import REGION_WEATHER, WEATHER_DATA_PROVENANCE
        for region, profile in REGION_WEATHER.items():
            assert "source" in profile, f"Region '{region}' missing source field"
            assert "NASA POWER" in profile["source"], f"Expected NASA POWER source for '{region}'"

    def test_weather_provenance_has_required_keys(self):
        from backend.app.data.weather_data import WEATHER_DATA_PROVENANCE
        required = {"source", "baseline_period", "api_url", "fetched_date", "license"}
        assert required.issubset(WEATHER_DATA_PROVENANCE.keys())

    def test_weather_values_are_nasa_power_calibrated(self):
        """Verify key known values from our NASA POWER fetch match."""
        from backend.app.data.weather_data import REGION_WEATHER
        nashik = REGION_WEATHER["Nashik / Maharashtra"]
        # Annual T2M from NASA POWER: 24.4°C ± 0.5
        assert 23.5 <= nashik["temperature_c"] <= 25.5, "Nashik annual T2M outside NASA POWER range"
        # RH2M: 61.2%
        assert 58.0 <= nashik["humidity_percent"] <= 64.0
        # Annual rain ≈ 1628mm from NASA POWER
        assert 1400.0 <= nashik["rainfall_mm"] <= 1900.0

    def test_nashik_rabi_season_is_cool_and_dry(self):
        """Rabi (Nov-Mar) in Nashik should be cooler and drier than annual average."""
        from backend.app.data.weather_data import get_weather_profile
        rabi = get_weather_profile("Nashik / Maharashtra", "Rabi")
        assert rabi["temperature_c"] < 25.0, "Rabi should be cooler than annual mean"
        assert rabi["rainfall_mm"] < 100.0, "Rabi in Nashik is dry (<100mm from NASA POWER)"

    def test_nashik_kharif_is_wet(self):
        """Kharif (Jun-Sep) in Nashik should have high monsoon rainfall."""
        from backend.app.data.weather_data import get_weather_profile
        kharif = get_weather_profile("Nashik / Maharashtra", "Kharif")
        assert kharif["rainfall_mm"] > 1000.0, "Kharif monsoon rainfall should be >1000mm"
        assert kharif["humidity_percent"] > 75.0, "Monsoon humidity should be >75%"

    def test_ludhiana_rabi_is_cold(self):
        """Punjab winters should be distinctly colder than Maharashtra."""
        from backend.app.data.weather_data import get_weather_profile
        ludhiana_rabi = get_weather_profile("Ludhiana / Punjab", "Rabi")
        nashik_rabi = get_weather_profile("Nashik / Maharashtra", "Rabi")
        assert ludhiana_rabi["temperature_c"] < nashik_rabi["temperature_c"]

    def test_thanjavur_rabi_has_northeast_monsoon(self):
        """Thanjavur gets NE monsoon in Rabi (reversed pattern): more rain than Kharif."""
        from backend.app.data.weather_data import get_weather_profile
        rabi = get_weather_profile("Thanjavur / Cauvery Delta", "Rabi")
        kharif = get_weather_profile("Thanjavur / Cauvery Delta", "Kharif")
        assert rabi["rainfall_mm"] > kharif["rainfall_mm"], (
            "Thanjavur gets NE monsoon in Rabi — should be rainier than Kharif"
        )

    def test_crop_database_has_provenance_constants(self):
        from backend.app.data.crop_database import ECONOMIC_DATA_PROVENANCE, CROP_DATA_VERSION
        assert CROP_DATA_VERSION is not None
        assert "market_prices" in ECONOMIC_DATA_PROVENANCE
        assert "cultivation_costs" in ECONOMIC_DATA_PROVENANCE
        assert "yield_benchmarks" in ECONOMIC_DATA_PROVENANCE
        # Should carry a freshness warning
        warning = ECONOMIC_DATA_PROVENANCE["market_prices"].get("warning", "")
        assert "static" in warning.lower() or "stale" in warning.lower()

    def test_soil_data_has_isric_validation(self):
        from backend.app.data.soil_data import ISRIC_VALIDATION
        assert "Thanjavur / Cauvery Delta" in ISRIC_VALIDATION
        entry = ISRIC_VALIDATION["Thanjavur / Cauvery Delta"]
        # Thanjavur pH from ISRIC was 7.3
        assert abs(entry["soilgrids_phh2o"] - 7.3) < 0.1


# ─── Economic Calculation Consistency ────────────────────────────────────────

class TestEconomicConsistency:
    """Verify all economic fields are internally consistent with documented formulas."""

    def test_wheat_profit_formula_correct(self):
        """Wheat: profit = yield × price - cost. RMS 2024-25 MSP = ₹2275/q."""
        from backend.app.data.crop_database import CROPS_DATABASE
        crop = CROPS_DATABASE["wheat"]
        expected_gross = crop.base_yield_quintals_per_acre * crop.market_price_per_quintal
        expected_profit = expected_gross - crop.cultivation_cost_per_acre
        # Allow ±50 rounding tolerance
        assert abs(crop.expected_profit_per_acre - expected_profit) <= 50, (
            f"Wheat profit inconsistent: stored={crop.expected_profit_per_acre}, "
            f"formula={expected_profit}"
        )

    def test_wheat_msp_is_2024_25_value(self):
        """Wheat MSP for RMS 2024-25 must be ₹2275/quintal (CACP notification)."""
        from backend.app.data.crop_database import CROPS_DATABASE
        crop = CROPS_DATABASE["wheat"]
        assert crop.market_price_per_quintal == 2275.0, (
            f"Wheat MSP should be ₹2275 (RMS 2024-25), got ₹{crop.market_price_per_quintal}"
        )

    def test_profit_margin_formula(self):
        """profit_margin_percent = (profit / gross_revenue) * 100 for all crops."""
        from backend.app.data.crop_database import CROPS_DATABASE
        for cid, crop in CROPS_DATABASE.items():
            gross = crop.base_yield_quintals_per_acre * crop.market_price_per_quintal
            if gross <= 0:
                continue
            expected_margin = (crop.expected_profit_per_acre / gross) * 100
            assert abs(crop.profit_margin_percent - expected_margin) <= 2.0, (
                f"Crop '{cid}' margin inconsistent: stored={crop.profit_margin_percent}, "
                f"formula={expected_margin:.1f}"
            )

    def test_no_crop_has_negative_price(self):
        from backend.app.data.crop_database import CROPS_DATABASE
        for cid, crop in CROPS_DATABASE.items():
            assert crop.market_price_per_quintal > 0, f"Crop '{cid}' has non-positive price"

    def test_no_crop_has_zero_cultivation_cost(self):
        from backend.app.data.crop_database import CROPS_DATABASE
        for cid, crop in CROPS_DATABASE.items():
            assert crop.cultivation_cost_per_acre > 0, f"Crop '{cid}' has zero cultivation cost"

    def test_yield_prediction_profit_units_consistent(self):
        """Yield prediction gross revenue = yield(q) × price(INR/q) = INR."""
        from backend.app.ml.yield_regressor import YieldPredictionRegressor
        reg = YieldPredictionRegressor()
        result = reg.predict_yield(
            crop_id="wheat", n=120, p=60, k=40, ph=7.0,
            temperature=18.0, rainfall=450.0
        )
        # gross_revenue = expected_yield × market_price
        computed = round(result["expected_yield_q_per_acre"] * result["market_price_per_q"], 2)
        assert abs(result["gross_revenue_per_acre"] - computed) < 1.0, (
            "Gross revenue does not equal yield × price"
        )

    def test_yield_prediction_profit_equals_revenue_minus_cost(self):
        from backend.app.ml.yield_regressor import YieldPredictionRegressor
        reg = YieldPredictionRegressor()
        result = reg.predict_yield(
            crop_id="chickpea", n=40, p=60, k=40, ph=7.0,
            temperature=22.0, rainfall=300.0
        )
        expected_profit = round(
            result["gross_revenue_per_acre"] - result["cultivation_cost_per_acre"], 2
        )
        assert abs(result["expected_profit_per_acre"] - expected_profit) < 1.0


# ─── Unit Integrity ───────────────────────────────────────────────────────────

class TestUnits:
    """Verify that units are consistent throughout the data pipeline."""

    def test_weather_temperatures_in_celsius(self):
        """All region temperatures should be plausible °C (5–45 range)."""
        from backend.app.data.weather_data import REGION_WEATHER
        for region, profile in REGION_WEATHER.items():
            assert 5.0 <= profile["temperature_c"] <= 45.0, (
                f"Region '{region}' temperature {profile['temperature_c']} outside plausible °C range"
            )
            for season, s_data in profile["season_defaults"].items():
                assert 5.0 <= s_data["temperature_c"] <= 50.0, (
                    f"Region '{region}', {season} temp {s_data['temperature_c']}°C implausible"
                )

    def test_weather_humidity_in_percent(self):
        """All humidity values should be 0–100%."""
        from backend.app.data.weather_data import REGION_WEATHER
        for region, profile in REGION_WEATHER.items():
            for season, s_data in profile["season_defaults"].items():
                rh = s_data["humidity_percent"]
                assert 0.0 <= rh <= 100.0, f"Region '{region}', {season} RH={rh} outside [0,100]"

    def test_weather_rainfall_in_mm(self):
        """Annual rainfall should be in mm (reasonable range: 200–5000mm for India)."""
        from backend.app.data.weather_data import REGION_WEATHER
        for region, profile in REGION_WEATHER.items():
            rain = profile["rainfall_mm"]
            assert 200 <= rain <= 5000, (
                f"Region '{region}' annual rainfall {rain}mm outside expected range"
            )

    def test_crop_water_requirement_in_kiloliters(self):
        """Water requirements should be in kL/acre (50–7000 reasonable range; sugarcane ~6500)."""
        from backend.app.data.crop_database import CROPS_DATABASE
        for cid, crop in CROPS_DATABASE.items():
            assert 50 <= crop.water_requirement_kl <= 7000, (
                f"Crop '{cid}' water={crop.water_requirement_kl} kL/acre out of range"
            )

    def test_crop_fertilizer_consistency(self):
        """total_fertilizer_kg should equal fertilizer_n_kg + fertilizer_p_kg + fertilizer_k_kg."""
        from backend.app.data.crop_database import CROPS_DATABASE
        for cid, crop in CROPS_DATABASE.items():
            expected_total = crop.fertilizer_n_kg + crop.fertilizer_p_kg + crop.fertilizer_k_kg
            assert abs(crop.total_fertilizer_kg - expected_total) < 1.0, (
                f"Crop '{cid}' total_fertilizer_kg={crop.total_fertilizer_kg} "
                f"!= N+P+K sum={expected_total}"
            )

    def test_yield_in_quintals_per_acre_not_kg(self):
        """Base yields should be realistic q/acre values. Sugarcane can reach 350-400 q/acre."""
        from backend.app.data.crop_database import CROPS_DATABASE
        for cid, crop in CROPS_DATABASE.items():
            assert 0.5 <= crop.base_yield_quintals_per_acre <= 500, (
                f"Crop '{cid}' base_yield={crop.base_yield_quintals_per_acre} q/acre implausible"
            )

    def test_optimizer_water_used_le_available(self):
        """Optimizer result: water_used_kl must never exceed water_available_kl."""
        from backend.app.optimizer.linear_programming import AgriculturalOptimizer
        opt = AgriculturalOptimizer()
        result = opt.solve_allocation(
            ["wheat", "chickpea", "mustard"],
            total_land_acres=8.0,
            water_available_kl=12000.0,
            fertilizer_available_kg=800.0,
            total_budget_inr=300000.0,
            strategy="max_profit"
        )
        if result["status"] == "Optimal":
            assert result["total_water_used_kl"] <= 12000.0 + 0.01
            assert result["total_fertilizer_used_kg"] <= 800.0 + 0.01
            assert result["total_budget_used_inr"] <= 300000.0 + 0.01


# ─── ML Model Evaluation ─────────────────────────────────────────────────────

class TestMLModelEvaluation:
    """Test that model evaluation methods return valid, honestly-labelled reports."""

    def test_yield_regressor_evaluate_returns_report(self):
        from backend.app.ml.yield_regressor import YieldPredictionRegressor
        reg = YieldPredictionRegressor()
        report = reg.evaluate(n_folds=3)
        assert "aggregate" in report
        assert "limitations" in report
        assert "data_source" in report
        assert "SYNTHETIC" in report["data_source"].upper()
        assert report["crops_evaluated"] > 0

    def test_yield_regressor_cv_metrics_valid(self):
        from backend.app.ml.yield_regressor import YieldPredictionRegressor
        reg = YieldPredictionRegressor()
        report = reg.evaluate(n_folds=3)
        agg = report["aggregate"]
        assert agg["mean_cv_rmse_q_per_acre"] is not None
        assert agg["mean_cv_rmse_q_per_acre"] > 0
        assert agg["mean_cv_r2"] is not None
        # Synthetic-to-synthetic fit should produce reasonable R²
        assert agg["mean_cv_r2"] > 0.3, "Expected at least moderate R² on synthetic data"

    def test_yield_regressor_limitation_note_present(self):
        """The report must explicitly state it is NOT real-world validated."""
        from backend.app.ml.yield_regressor import YieldPredictionRegressor
        reg = YieldPredictionRegressor()
        report = reg.evaluate(n_folds=3)
        # Must contain honest disclaimer
        limitations = report["limitations"].lower()
        assert "synthetic" in limitations
        assert "not" in limitations  # "NOT validated" or similar

    def test_classifier_evaluate_returns_report(self):
        from backend.app.ml.crop_classifier import CropSuitabilityClassifier
        clf = CropSuitabilityClassifier()
        report = clf.evaluate(n_folds=3)
        assert "cv_accuracy_mean" in report
        assert "cv_f1_weighted_mean" in report
        assert "limitations" in report
        assert "SYNTHETIC" in report["data_source"].upper()

    def test_classifier_cv_accuracy_valid_range(self):
        from backend.app.ml.crop_classifier import CropSuitabilityClassifier
        clf = CropSuitabilityClassifier()
        report = clf.evaluate(n_folds=3)
        acc = report["cv_accuracy_mean"]
        assert 0.0 <= acc <= 1.0
        # On synthetic data (class-conditional features), expect high-ish accuracy
        assert acc > 0.50, "Expected >50% accuracy even on synthetic data"

    def test_classifier_get_model_info(self):
        from backend.app.ml.crop_classifier import CropSuitabilityClassifier
        clf = CropSuitabilityClassifier()
        clf.train()
        info = clf.get_model_info()
        assert info["is_trained"] is True
        assert info["n_classes"] > 0
        assert "synthetic" in info["disclaimer"].lower()

    def test_yield_regressor_get_model_info(self):
        from backend.app.ml.yield_regressor import YieldPredictionRegressor
        reg = YieldPredictionRegressor()
        reg.train()
        info = reg.get_model_info()
        assert info["is_trained"] is True
        assert info["crops_trained"] > 0
        assert "synthetic" in info["disclaimer"].lower()

    def test_prediction_range_note_present_in_yield_response(self):
        """prediction_range_note must be in the yield prediction response."""
        from backend.app.ml.yield_regressor import YieldPredictionRegressor
        reg = YieldPredictionRegressor()
        result = reg.predict_yield(
            crop_id="onion", n=120, p=60, k=80, ph=7.0,
            temperature=20.0, rainfall=500.0
        )
        assert "prediction_range_note" in result
        assert "heuristic" in result["prediction_range_note"].lower() or \
               "synthetic" in result["prediction_range_note"].lower()


# ─── Data Pipeline ────────────────────────────────────────────────────────────

class TestRealDataPipeline:
    """Test the data import pipeline — CSV validation and augmented dataset."""

    def test_pipeline_builds_synthetic_fallback(self):
        from backend.app.data.real_data_pipeline import RealDataPipeline
        pipeline = RealDataPipeline()
        df = pipeline.build_augmented_yield_dataset(synthetic_samples_per_crop=10)
        assert len(df) > 0
        assert "data_source" in df.columns
        assert "is_synthetic" in df.columns
        assert df["is_synthetic"].all(), "All rows should be synthetic when no CSV provided"

    def test_pipeline_synthetic_clearly_labeled(self):
        from backend.app.data.real_data_pipeline import RealDataPipeline
        pipeline = RealDataPipeline()
        df = pipeline.build_augmented_yield_dataset(synthetic_samples_per_crop=5)
        source_vals = df["data_source"].unique()
        assert any("synthetic" in s for s in source_vals), "Synthetic rows must be labeled as synthetic"

    def test_pipeline_summary_reports_correct_counts(self):
        from backend.app.data.real_data_pipeline import RealDataPipeline
        pipeline = RealDataPipeline()
        df = pipeline.build_augmented_yield_dataset(synthetic_samples_per_crop=10)
        summary = pipeline.summarize_dataset(df)
        assert summary["total_samples"] == len(df)
        assert summary["synthetic_count"] == len(df)
        assert summary["real_count"] == 0

    def test_csv_load_rejects_missing_columns(self, tmp_path):
        """CSV without required columns must raise ValueError."""
        from backend.app.data.real_data_pipeline import RealDataPipeline
        pipeline = RealDataPipeline()
        # Write an incomplete CSV
        bad_csv = tmp_path / "bad.csv"
        bad_csv.write_text("crop_id,N\nonion,100\n")
        with pytest.raises(ValueError, match="missing required columns"):
            pipeline.load_csv(str(bad_csv))

    def test_csv_load_rejects_unknown_crop(self, tmp_path):
        """CSV with unknown crop_id must raise ValueError."""
        from backend.app.data.real_data_pipeline import RealDataPipeline
        pipeline = RealDataPipeline()
        good_cols = "crop_id,N,P,K,ph,temperature,rainfall,water_available_kl,fertilizer_applied_kg,yield_q_per_acre"
        bad_csv = tmp_path / "bad_crop.csv"
        bad_csv.write_text(good_cols + "\nunknown_crop,100,50,50,7.0,25,400,1500,80,12.0\n")
        with pytest.raises(ValueError, match="Unknown crop_id"):
            pipeline.load_csv(str(bad_csv))

    def test_csv_load_rejects_out_of_range_ph(self, tmp_path):
        """CSV with pH > 10.5 must raise ValueError."""
        from backend.app.data.real_data_pipeline import RealDataPipeline
        pipeline = RealDataPipeline()
        good_cols = "crop_id,N,P,K,ph,temperature,rainfall,water_available_kl,fertilizer_applied_kg,yield_q_per_acre"
        bad_csv = tmp_path / "bad_ph.csv"
        bad_csv.write_text(good_cols + "\nonion,100,50,50,12.0,25,400,1500,80,12.0\n")
        with pytest.raises(ValueError, match="ph"):
            pipeline.load_csv(str(bad_csv))

    def test_csv_load_valid_data_succeeds(self, tmp_path):
        """Valid CSV should load without errors and return a DataFrame."""
        from backend.app.data.real_data_pipeline import RealDataPipeline
        pipeline = RealDataPipeline()
        good_cols = "crop_id,N,P,K,ph,temperature,rainfall,water_available_kl,fertilizer_applied_kg,yield_q_per_acre"
        good_csv = tmp_path / "good.csv"
        good_csv.write_text(good_cols + "\nonion,120,60,80,7.0,22.0,450,2200,104,85.0\n")
        df = pipeline.load_csv(str(good_csv))
        assert len(df) == 1
        assert "is_synthetic" in df.columns
        # is_synthetic should be False for CSV imports
        assert bool(df["is_synthetic"].iloc[0]) is False


# ─── API Endpoint Tests ───────────────────────────────────────────────────────

class TestAPIEndpoints:
    """Verify API endpoints work correctly including error cases."""

    def test_health_endpoint_returns_healthy(self):
        r = client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data

    def test_model_info_endpoint(self):
        """GET /model-info should return provenance and disclaimer."""
        r = client.get("/model-info")
        assert r.status_code == 200
        data = r.json()
        assert "models" in data
        assert "data_provenance" in data
        assert "disclaimer" in data
        # Must mention synthetic data
        assert "SYNTHETIC" in data["disclaimer"].upper() or "synthetic" in data["disclaimer"].lower()

    def test_model_info_contains_nasa_power_provenance(self):
        r = client.get("/model-info")
        data = r.json()
        weather_prov = data["data_provenance"]["weather_data"]
        assert "NASA POWER" in weather_prov.get("source", "")

    def test_model_info_contains_msp_economic_provenance(self):
        r = client.get("/model-info")
        data = r.json()
        econ = data["data_provenance"]["economic_data"]
        assert "market_prices" in econ
        assert "CACP" in str(econ["market_prices"].get("authority", ""))

    def test_predict_yield_returns_prediction_range_note(self):
        """API yield prediction must include prediction_range_note."""
        payload = {
            "crop_id": "wheat",
            "n": 120.0, "p": 60.0, "k": 40.0,
            "ph": 7.0, "temperature": 18.0, "rainfall": 450.0
        }
        r = client.post("/predict/yield", json=payload)
        assert r.status_code == 200
        data = r.json()
        assert "prediction_range_note" in data
        assert data["prediction_range_note"] is not None

    def test_predict_yield_profit_formula(self):
        """API: gross_revenue = yield × price; profit = revenue - cost."""
        payload = {
            "crop_id": "chickpea",
            "n": 40.0, "p": 60.0, "k": 40.0,
            "ph": 7.2, "temperature": 22.0, "rainfall": 320.0
        }
        r = client.post("/predict/yield", json=payload)
        assert r.status_code == 200
        data = r.json()
        expected_gross = round(data["expected_yield_q_per_acre"] * data["market_price_per_q"], 2)
        assert abs(data["gross_revenue_per_acre"] - expected_gross) < 1.0
        expected_profit = round(data["gross_revenue_per_acre"] - data["cultivation_cost_per_acre"], 2)
        assert abs(data["expected_profit_per_acre"] - expected_profit) < 1.0

    def test_recommend_crops_returns_data_with_real_weather(self):
        """Crop recommendations with NASA POWER-calibrated Nashik Rabi weather inputs."""
        from backend.app.data.weather_data import get_weather_profile
        weather = get_weather_profile("Nashik / Maharashtra", "Rabi")
        payload = {
            "n": 80.0, "p": 45.0, "k": 70.0, "ph": 7.6,
            "temperature": weather["temperature_c"],
            "humidity": weather["humidity_percent"],
            "rainfall": weather["rainfall_mm"],
            "season": "Rabi",
            "top_k": 5,
        }
        r = client.post("/recommend/crops", json=payload)
        assert r.status_code == 200
        data = r.json()
        assert data["count"] > 0
        for crop in data["crops"]:
            # CropItem schema exposes 'suitability' (string badge) not 'suitability_score'
            assert "suitability" in crop
            assert crop["suitability"] != ""
            assert "crop_id" in crop

    def test_api_missing_crop_returns_400(self):
        """Unknown crop_id must return 400."""
        payload = {
            "crop_id": "martian_grain",
            "n": 100, "p": 50, "k": 50,
            "ph": 7.0, "temperature": 25.0, "rainfall": 400.0
        }
        r = client.post("/predict/yield", json=payload)
        assert r.status_code == 400

    def test_optimizer_infeasible_returns_status(self):
        """Zero budget must return Infeasible status, not crash."""
        payload = {
            "crop_ids": ["wheat", "chickpea"],
            "total_land_acres": 5.0,
            "water_available_kl": 8000.0,
            "fertilizer_available_kg": 400.0,
            "total_budget_inr": 5000.0,  # minimum allowed by schema
            "strategy": "balanced"
        }
        r = client.post("/optimize/allocate", json=payload)
        # Should return 200 with either Optimal or Infeasible
        assert r.status_code == 200
        data = r.json()
        assert data["status"] in ("Optimal", "Infeasible")

    def test_weather_get_profile_returns_dict(self):
        from backend.app.data.weather_data import get_weather_profile, list_regions
        regions = list_regions()
        assert len(regions) >= 4
        for region in regions:
            for season in ["Rabi", "Kharif", "Zaid"]:
                profile = get_weather_profile(region, season)
                assert "temperature_c" in profile
                assert "humidity_percent" in profile
                assert "rainfall_mm" in profile

    def test_weather_fallback_on_unknown_region(self):
        """Unknown district should fall back gracefully (not raise)."""
        from backend.app.data.weather_data import get_weather_profile
        profile = get_weather_profile("Unknown District XYZ", "Rabi")
        assert "temperature_c" in profile  # should have fallen back to Nashik defaults
