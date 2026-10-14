"""
Unit tests for Machine Learning models and Linear Programming Optimizer.
"""

import pytest
from backend.app.ml.crop_classifier import CropSuitabilityClassifier
from backend.app.ml.yield_regressor import YieldPredictionRegressor
from backend.app.optimizer.linear_programming import AgriculturalOptimizer


def test_crop_suitability_classifier():
    classifier = CropSuitabilityClassifier()
    classifier.train()

    # Predict for typical Rabi soil/weather in Maharashtra
    results = classifier.predict_suitability(
        n=80.0,
        p=45.0,
        k=70.0,
        ph=7.2,
        temperature=22.0,
        humidity=60.0,
        rainfall=400.0,
        season="Rabi",
        top_k=6
    )

    assert len(results) > 0
    top_crop = results[0]
    assert "crop_id" in top_crop
    assert "suitability_score" in top_crop
    assert 40 <= top_crop["suitability_score"] <= 100
    assert top_crop["status"] in ["in", "out"]
    assert top_crop["water"] in ["Low", "Medium", "High", "Very High"]


def test_yield_regressor():
    regressor = YieldPredictionRegressor()
    regressor.train()

    pred = regressor.predict_yield(
        crop_id="wheat",
        n=120.0,
        p=60.0,
        k=40.0,
        ph=6.8,
        temperature=18.0,
        rainfall=450.0,
        water_available_kl=1600.0,
        fertilizer_applied_kg=88.0
    )

    assert pred["crop_id"] == "wheat"
    assert pred["expected_yield_q_per_acre"] > 0
    assert pred["expected_profit_per_acre"] > 0
    assert pred["confidence_interval_95"]["lower_q_per_acre"] <= pred["expected_yield_q_per_acre"]
    assert pred["confidence_interval_95"]["upper_q_per_acre"] >= pred["expected_yield_q_per_acre"]


def test_optimizer_balanced_allocation():
    optimizer = AgriculturalOptimizer()
    result = optimizer.solve_allocation(
        crop_ids=["onion", "wheat", "chickpea", "mustard"],
        total_land_acres=10.0,
        water_available_kl=16000.0,
        fertilizer_available_kg=1000.0,
        total_budget_inr=400000.0,
        strategy="balanced"
    )

    assert result["strategy"] == "Balanced"
    assert result["total_land_allocated_acres"] <= 10.05
    assert result["total_water_used_kl"] <= 16000.0
    assert result["total_budget_used_inr"] <= 400000.0
    assert result["expected_net_profit_inr"] > 100000.0
    assert len(result["crops"]) >= 3


def test_optimizer_strategy_comparison():
    optimizer = AgriculturalOptimizer()
    comparisons = optimizer.compare_strategies(
        crop_ids=["onion", "wheat", "chickpea", "mustard"],
        total_land_acres=10.0,
        water_available_kl=16000.0,
        fertilizer_available_kg=1000.0,
        total_budget_inr=400000.0
    )

    assert len(comparisons) == 4
    strategies_found = {c["strategy"].lower() for c in comparisons}
    assert "balanced" in strategies_found
    assert "max profit" in strategies_found
    assert "water saver" in strategies_found
    assert "low budget" in strategies_found
