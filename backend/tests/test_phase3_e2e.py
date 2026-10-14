"""
Phase 3 End-to-End Agricultural Workflow Regression Tests.

Traces the complete farmer workflow:
  Farm inputs → Crop recommendations → Yield prediction → Resource optimization
  → Cost/revenue/profit → API/UI consistency

Uses FastAPI TestClient (no live server required).
"""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

# ── Auth helpers ──────────────────────────────────────────────────────────────

def get_auth_token() -> str:
    r = client.post("/auth/login", json={
        "email": "ramesh.patil@gmail.com", "password": "terra123"
    })
    assert r.status_code == 200, f"Login failed: {r.text}"
    return r.json()["access_token"]

def auth_headers() -> dict:
    return {"Authorization": f"Bearer {get_auth_token()}"}


# ══════════════════════════════════════════════════════════════════════════════
# 1. FULL FARMER WORKFLOW — HAPPY PATH (sufficient resources)
# ══════════════════════════════════════════════════════════════════════════════

class TestCompleteWorkflow:
    """
    Traces: soil input → crop recommendation → optimizer → profit math.
    Farm: 10 acres, 16000 kL water, 1000 kg fertilizer, ₹4L budget.
    """

    def test_step1_login(self):
        r = client.post("/auth/login", json={
            "email": "ramesh.patil@gmail.com", "password": "terra123"
        })
        assert r.status_code == 200
        assert "access_token" in r.json()

    def test_step2_recommend_crops_typical_nashik_rabi(self):
        """Realistic Nashik Rabi soil+weather → at least 3 recommendations."""
        r = client.post("/recommend/crops", json={
            "n": 80, "p": 45, "k": 70, "ph": 7.2,
            "temperature": 22.7, "humidity": 43.4, "rainfall": 31.0,
            "season": "Rabi", "top_k": 6
        })
        assert r.status_code == 200
        data = r.json()
        assert data["count"] >= 3
        for crop in data["crops"]:
            assert "crop_id" in crop
            assert "suitability" in crop
            assert "yield" in crop
            assert "profit" in crop
            assert "sow" in crop

    def test_step3_optimizer_with_recommended_crops(self):
        """Optimizer with recommended crops should produce valid allocation."""
        # Get recommendations first
        rec = client.post("/recommend/crops", json={
            "n": 80, "p": 45, "k": 70, "ph": 7.2,
            "temperature": 22.7, "humidity": 43.4, "rainfall": 31.0,
            "season": "Rabi", "top_k": 4
        })
        crop_ids = [c["crop_id"] for c in rec.json()["crops"][:4]]

        opt = client.post("/optimize/allocate", json={
            "crop_ids": crop_ids,
            "total_land_acres": 10.0,
            "water_available_kl": 16000.0,
            "fertilizer_available_kg": 1000.0,
            "total_budget_inr": 400000.0,
            "strategy": "balanced"
        })
        assert opt.status_code == 200
        d = opt.json()
        assert d["status"] == "Optimal"
        assert len(d["crops"]) > 0

    def test_step4_allocation_never_exceeds_land(self):
        """Allocated land must NEVER exceed available land."""
        r = client.post("/optimize/allocate", json={
            "crop_ids": ["onion", "wheat", "chickpea", "mustard"],
            "total_land_acres": 10.0,
            "water_available_kl": 16000.0,
            "fertilizer_available_kg": 1000.0,
            "total_budget_inr": 400000.0,
            "strategy": "balanced"
        })
        d = r.json()
        assert d["status"] == "Optimal"
        assert d["total_land_allocated_acres"] <= 10.0 + 0.01

    def test_step5_allocation_never_exceeds_water(self):
        """Water used must NEVER exceed water_available_kl."""
        for strategy in ["balanced", "max_profit", "water_saver", "low_budget"]:
            r = client.post("/optimize/allocate", json={
                "crop_ids": ["onion", "wheat", "chickpea", "mustard"],
                "total_land_acres": 10.0,
                "water_available_kl": 16000.0,
                "fertilizer_available_kg": 1000.0,
                "total_budget_inr": 400000.0,
                "strategy": strategy
            })
            d = r.json()
            if d["status"] == "Optimal":
                assert d["total_water_used_kl"] <= 16000.0 + 1.0, \
                    f"Strategy {strategy}: water violation {d['total_water_used_kl']}"

    def test_step6_allocation_never_exceeds_fertilizer(self):
        for strategy in ["balanced", "max_profit", "water_saver", "low_budget"]:
            r = client.post("/optimize/allocate", json={
                "crop_ids": ["onion", "wheat", "chickpea", "mustard"],
                "total_land_acres": 10.0,
                "water_available_kl": 16000.0,
                "fertilizer_available_kg": 1000.0,
                "total_budget_inr": 400000.0,
                "strategy": strategy
            })
            d = r.json()
            if d["status"] == "Optimal":
                assert d["total_fertilizer_used_kg"] <= 1000.0 + 0.5, \
                    f"Strategy {strategy}: fertilizer violation {d['total_fertilizer_used_kg']}"

    def test_step7_allocation_never_exceeds_budget(self):
        for strategy in ["balanced", "max_profit", "water_saver", "low_budget"]:
            r = client.post("/optimize/allocate", json={
                "crop_ids": ["onion", "wheat", "chickpea", "mustard"],
                "total_land_acres": 10.0,
                "water_available_kl": 16000.0,
                "fertilizer_available_kg": 1000.0,
                "total_budget_inr": 400000.0,
                "strategy": strategy
            })
            d = r.json()
            if d["status"] == "Optimal":
                assert d["total_budget_used_inr"] <= 400000.0 + 100.0, \
                    f"Strategy {strategy}: budget violation {d['total_budget_used_inr']}"

    def test_step8_profit_math_consistency(self):
        """Sum of per-crop profits = reported total net profit."""
        r = client.post("/optimize/allocate", json={
            "crop_ids": ["onion", "wheat", "chickpea", "mustard"],
            "total_land_acres": 10.0,
            "water_available_kl": 16000.0,
            "fertilizer_available_kg": 1000.0,
            "total_budget_inr": 400000.0,
            "strategy": "balanced"
        })
        d = r.json()
        assert d["status"] == "Optimal"
        sum_profit = sum(c["expected_profit_inr"] for c in d["crops"])
        assert abs(sum_profit - d["expected_net_profit_inr"]) < 1.0, \
            f"Profit mismatch: sum={sum_profit}, reported={d['expected_net_profit_inr']}"

    def test_step9_yield_math_consistency(self):
        """Sum of per-crop yields = reported total production."""
        r = client.post("/optimize/allocate", json={
            "crop_ids": ["onion", "wheat", "chickpea", "mustard"],
            "total_land_acres": 10.0,
            "water_available_kl": 16000.0,
            "fertilizer_available_kg": 1000.0,
            "total_budget_inr": 400000.0,
            "strategy": "max_profit"
        })
        d = r.json()
        assert d["status"] == "Optimal"
        sum_yield = sum(c["expected_yield_q"] for c in d["crops"])
        assert abs(sum_yield - d["expected_total_production_q"]) < 0.5, \
            f"Yield mismatch: sum={sum_yield}, reported={d['expected_total_production_q']}"

    def test_step10_budget_math_consistency(self):
        """Sum of per-crop costs = reported total budget used."""
        r = client.post("/optimize/allocate", json={
            "crop_ids": ["onion", "wheat", "chickpea", "mustard"],
            "total_land_acres": 10.0,
            "water_available_kl": 16000.0,
            "fertilizer_available_kg": 1000.0,
            "total_budget_inr": 400000.0,
            "strategy": "low_budget"
        })
        d = r.json()
        if d["status"] != "Optimal":
            pytest.skip("Infeasible for this scenario")
        sum_cost = sum(c["cost_inr"] for c in d["crops"])
        assert abs(sum_cost - d["total_budget_used_inr"]) < 1.0, \
            f"Budget mismatch: sum={sum_cost}, reported={d['total_budget_used_inr']}"

    def test_step11_yield_prediction_profit_formula(self):
        """Yield prediction: gross_revenue = yield × price; profit = revenue − cost."""
        r = client.post("/predict/yield", json={
            "crop_id": "onion", "n": 120, "p": 60, "k": 80,
            "ph": 7.0, "temperature": 22.0, "rainfall": 450.0
        })
        assert r.status_code == 200
        d = r.json()
        expected_gross = round(d["expected_yield_q_per_acre"] * d["market_price_per_q"], 2)
        assert abs(d["gross_revenue_per_acre"] - expected_gross) < 1.0, \
            f"Revenue = yield × price violated: {d['gross_revenue_per_acre']} != {expected_gross}"
        expected_profit = round(d["gross_revenue_per_acre"] - d["cultivation_cost_per_acre"], 2)
        assert abs(d["expected_profit_per_acre"] - expected_profit) < 1.0, \
            f"Profit = revenue - cost violated: {d['expected_profit_per_acre']} != {expected_profit}"

    def test_step12_prediction_has_disclaimer(self):
        """Every yield prediction must have prediction_range_note."""
        for crop_id in ["wheat", "chickpea", "onion", "mustard"]:
            r = client.post("/predict/yield", json={
                "crop_id": crop_id, "n": 80, "p": 45, "k": 70,
                "ph": 7.0, "temperature": 22.0, "rainfall": 400.0
            })
            assert r.status_code == 200
            note = r.json().get("prediction_range_note", "")
            assert note, f"Missing prediction_range_note for {crop_id}"
            assert len(note) > 20, f"prediction_range_note too short for {crop_id}: {note}"


# ══════════════════════════════════════════════════════════════════════════════
# 2. CONSTRAINED FARM SCENARIOS
# ══════════════════════════════════════════════════════════════════════════════

class TestConstrainedFarms:

    def test_water_constrained_farm(self):
        """Very low water (2000 kL for 10 acres) — optimizer must stay within."""
        r = client.post("/optimize/allocate", json={
            "crop_ids": ["mustard", "chickpea", "wheat"],
            "total_land_acres": 10.0,
            "water_available_kl": 2000.0,
            "fertilizer_available_kg": 800.0,
            "total_budget_inr": 300000.0,
            "strategy": "water_saver"
        })
        d = r.json()
        if d["status"] == "Optimal":
            assert d["total_water_used_kl"] <= 2000.0 + 1.0
        else:
            assert d["status"] == "Infeasible"
            assert d.get("error"), "Infeasible must include error message"

    def test_fertilizer_constrained_farm(self):
        """Very low fertilizer (50 kg for 10 acres) — must not exceed."""
        r = client.post("/optimize/allocate", json={
            "crop_ids": ["mustard", "chickpea", "wheat"],
            "total_land_acres": 10.0,
            "water_available_kl": 16000.0,
            "fertilizer_available_kg": 50.0,
            "total_budget_inr": 300000.0,
            "strategy": "balanced"
        })
        d = r.json()
        if d["status"] == "Optimal":
            assert d["total_fertilizer_used_kg"] <= 50.0 + 0.5
        else:
            assert d["status"] == "Infeasible"

    def test_land_constrained_small_farm(self):
        """1-acre farm — allocation must stay within 1 acre."""
        r = client.post("/optimize/allocate", json={
            "crop_ids": ["onion", "chickpea"],
            "total_land_acres": 1.0,
            "water_available_kl": 2500.0,
            "fertilizer_available_kg": 200.0,
            "total_budget_inr": 80000.0,
            "strategy": "max_profit"
        })
        d = r.json()
        if d["status"] == "Optimal":
            assert d["total_land_allocated_acres"] <= 1.0 + 0.01
            for c in d["crops"]:
                assert c["acres"] <= 1.0 + 0.01

    def test_budget_constrained_farm(self):
        """Minimal budget (₹20,000 for 5 acres) — must not exceed."""
        r = client.post("/optimize/allocate", json={
            "crop_ids": ["chickpea", "mustard", "sorghum"],
            "total_land_acres": 5.0,
            "water_available_kl": 8000.0,
            "fertilizer_available_kg": 500.0,
            "total_budget_inr": 20000.0,
            "strategy": "low_budget"
        })
        d = r.json()
        if d["status"] == "Optimal":
            assert d["total_budget_used_inr"] <= 20000.0 + 100.0
        else:
            assert d["status"] == "Infeasible"

    def test_multiple_tight_constraints(self):
        """All constraints tight simultaneously — must not violate any."""
        # Barely enough water for 1 mustard + 1 chickpea acre
        r = client.post("/optimize/allocate", json={
            "crop_ids": ["mustard", "chickpea"],
            "total_land_acres": 2.0,
            "water_available_kl": 2000.0,
            "fertilizer_available_kg": 120.0,
            "total_budget_inr": 40000.0,
            "strategy": "water_saver"
        })
        d = r.json()
        if d["status"] == "Optimal":
            assert d["total_land_allocated_acres"] <= 2.0 + 0.01
            assert d["total_water_used_kl"] <= 2000.0 + 1.0
            assert d["total_fertilizer_used_kg"] <= 120.0 + 0.5
            assert d["total_budget_used_inr"] <= 40000.0 + 100.0

    def test_single_crop_optimization(self):
        """Single crop allocation must work without error."""
        r = client.post("/optimize/allocate", json={
            "crop_ids": ["wheat"],
            "total_land_acres": 5.0,
            "water_available_kl": 8000.0,
            "fertilizer_available_kg": 400.0,
            "total_budget_inr": 100000.0,
            "strategy": "max_profit"
        })
        assert r.status_code == 200
        d = r.json()
        assert d["status"] in ("Optimal", "Infeasible")
        if d["status"] == "Optimal":
            assert d["total_land_allocated_acres"] <= 5.0 + 0.01


# ══════════════════════════════════════════════════════════════════════════════
# 3. INFEASIBLE INPUTS
# ══════════════════════════════════════════════════════════════════════════════

class TestInfeasibleInputs:

    def test_zero_budget_returns_infeasible(self):
        """Budget below schema minimum returns 422, not a fake result."""
        r = client.post("/optimize/allocate", json={
            "crop_ids": ["wheat"],
            "total_land_acres": 5.0,
            "water_available_kl": 8000.0,
            "fertilizer_available_kg": 400.0,
            "total_budget_inr": 100.0,   # below ge=5000 minimum
            "strategy": "balanced"
        })
        assert r.status_code == 422  # schema validation catches this

    def test_impossible_water_min_for_high_water_crops_only(self):
        """Onion (2200 kL/acre) with only 100 kL for 2 acres = infeasible."""
        r = client.post("/optimize/allocate", json={
            "crop_ids": ["onion"],
            "total_land_acres": 2.0,
            "water_available_kl": 100.0,
            "fertilizer_available_kg": 300.0,
            "total_budget_inr": 200000.0,
            "strategy": "balanced"
        })
        assert r.status_code == 200
        d = r.json()
        assert d["status"] == "Infeasible"
        assert d.get("error"), "Infeasible response must include error message"
        assert d["total_land_allocated_acres"] == 0.0
        assert d["expected_net_profit_inr"] == 0.0

    def test_unknown_strategy_returns_infeasible(self):
        """Unknown strategy must return Infeasible, never silently use balanced."""
        r = client.post("/optimize/allocate", json={
            "crop_ids": ["wheat", "chickpea"],
            "total_land_acres": 5.0,
            "water_available_kl": 8000.0,
            "fertilizer_available_kg": 500.0,
            "total_budget_inr": 200000.0,
            "strategy": "moon_farming"
        })
        assert r.status_code == 200
        d = r.json()
        assert d["status"] == "Infeasible"
        assert "Unknown strategy" in d.get("error", "")

    def test_unknown_crop_id_falls_back_with_warning(self):
        """All unknown crop IDs → falls back to defaults + warning field."""
        r = client.post("/optimize/allocate", json={
            "crop_ids": ["martian_grain", "moon_wheat"],
            "total_land_acres": 5.0,
            "water_available_kl": 8000.0,
            "fertilizer_available_kg": 500.0,
            "total_budget_inr": 200000.0,
            "strategy": "balanced"
        })
        assert r.status_code == 200
        d = r.json()
        # Must warn about unknown crops
        assert d.get("warning"), "Should warn about unknown crop IDs"

    def test_predict_yield_unknown_crop_returns_400(self):
        """Unknown crop_id must return 400, never a fabricated prediction."""
        r = client.post("/predict/yield", json={
            "crop_id": "kryptonite_corn",
            "n": 100, "p": 50, "k": 50, "ph": 7.0,
            "temperature": 25.0, "rainfall": 400.0
        })
        assert r.status_code == 400

    def test_infeasible_allocation_has_no_crops(self):
        """Infeasible result must have empty crops list, not a fake allocation."""
        r = client.post("/optimize/allocate", json={
            "crop_ids": ["onion"],
            "total_land_acres": 5.0,
            "water_available_kl": 100.0,   # impossible for onion
            "fertilizer_available_kg": 500.0,
            "total_budget_inr": 200000.0,
            "strategy": "max_profit"
        })
        d = r.json()
        assert d["status"] == "Infeasible"
        assert d["crops"] == [], "Infeasible must return empty crops list"

    def test_negative_npk_rejected(self):
        """Negative NPK values in yield prediction must be rejected."""
        r = client.post("/predict/yield", json={
            "crop_id": "wheat",
            "n": -10, "p": 50, "k": 50, "ph": 7.0,
            "temperature": 20.0, "rainfall": 400.0
        })
        assert r.status_code == 422

    def test_invalid_ph_rejected(self):
        """pH outside [3.5, 10.5] must be rejected."""
        r = client.post("/predict/yield", json={
            "crop_id": "wheat",
            "n": 80, "p": 50, "k": 50, "ph": 15.0,
            "temperature": 20.0, "rainfall": 400.0
        })
        assert r.status_code == 422


# ══════════════════════════════════════════════════════════════════════════════
# 4. PREDICTION → OPTIMIZER CONSISTENCY
# ══════════════════════════════════════════════════════════════════════════════

class TestPredictionOptimizerConsistency:
    """
    Both the yield predictor and optimizer use CROPS_DATABASE for crop-specific
    economic parameters. Verify they use the same source data.
    """

    def test_optimizer_crop_yield_matches_database(self):
        """Optimizer crop yield = acres × crop.base_yield_quintals_per_acre (from DB)."""
        from backend.app.data.crop_database import CROPS_DATABASE

        r = client.post("/optimize/allocate", json={
            "crop_ids": ["wheat", "chickpea"],
            "total_land_acres": 6.0,
            "water_available_kl": 10000.0,
            "fertilizer_available_kg": 600.0,
            "total_budget_inr": 200000.0,
            "strategy": "max_profit"
        })
        d = r.json()
        if d["status"] != "Optimal":
            pytest.skip("Infeasible — skip consistency check")

        for c in d["crops"]:
            crop_db = CROPS_DATABASE.get(c["crop_id"])
            if crop_db:
                expected_yield = round(c["acres"] * crop_db.base_yield_quintals_per_acre, 1)
                assert abs(c["expected_yield_q"] - expected_yield) < 0.2, (
                    f"{c['crop_id']}: optimizer yield {c['expected_yield_q']} "
                    f"≠ acres×db_yield {expected_yield}"
                )

    def test_optimizer_crop_cost_matches_database(self):
        """Optimizer cost_inr = acres × crop.cultivation_cost_per_acre (from DB)."""
        from backend.app.data.crop_database import CROPS_DATABASE

        r = client.post("/optimize/allocate", json={
            "crop_ids": ["onion", "mustard"],
            "total_land_acres": 4.0,
            "water_available_kl": 10000.0,
            "fertilizer_available_kg": 400.0,
            "total_budget_inr": 300000.0,
            "strategy": "balanced"
        })
        d = r.json()
        if d["status"] != "Optimal":
            pytest.skip("Infeasible — skip")

        for c in d["crops"]:
            crop_db = CROPS_DATABASE.get(c["crop_id"])
            if crop_db:
                expected_cost = round(c["acres"] * crop_db.cultivation_cost_per_acre, 2)
                assert abs(c["cost_inr"] - expected_cost) < 1.0, (
                    f"{c['crop_id']}: optimizer cost {c['cost_inr']} "
                    f"≠ acres×db_cost {expected_cost}"
                )

    def test_optimizer_profit_matches_database(self):
        """Optimizer profit = acres × expected_profit_per_acre (from DB)."""
        from backend.app.data.crop_database import CROPS_DATABASE

        r = client.post("/optimize/allocate", json={
            "crop_ids": ["onion", "chickpea", "mustard"],
            "total_land_acres": 6.0,
            "water_available_kl": 12000.0,
            "fertilizer_available_kg": 500.0,
            "total_budget_inr": 250000.0,
            "strategy": "balanced"
        })
        d = r.json()
        if d["status"] != "Optimal":
            pytest.skip("Infeasible — skip")

        for c in d["crops"]:
            crop_db = CROPS_DATABASE.get(c["crop_id"])
            if crop_db:
                expected_profit = round(c["acres"] * crop_db.expected_profit_per_acre, 2)
                assert abs(c["expected_profit_inr"] - expected_profit) < 1.0, (
                    f"{c['crop_id']}: optimizer profit {c['expected_profit_inr']} "
                    f"≠ acres×db_profit {expected_profit}"
                )

    def test_yield_predictor_and_db_are_compatible_units(self):
        """Yield predictor returns q/acre, optimizer uses same unit from DB."""
        from backend.app.data.crop_database import CROPS_DATABASE

        for crop_id in ["wheat", "chickpea", "onion"]:
            r = client.post("/predict/yield", json={
                "crop_id": crop_id, "n": 80, "p": 45, "k": 70,
                "ph": 7.0, "temperature": 22.0, "rainfall": 400.0
            })
            assert r.status_code == 200
            pred = r.json()
            db_crop = CROPS_DATABASE[crop_id]
            # Predictor yield should be within 3× of DB base (same ballpark)
            ratio = pred["expected_yield_q_per_acre"] / db_crop.base_yield_quintals_per_acre
            assert 0.2 <= ratio <= 5.0, (
                f"{crop_id}: predictor yield {pred['expected_yield_q_per_acre']} "
                f"vs DB base {db_crop.base_yield_quintals_per_acre} — unit mismatch likely"
            )


# ══════════════════════════════════════════════════════════════════════════════
# 5. STRATEGY COMPARISON CONSISTENCY
# ══════════════════════════════════════════════════════════════════════════════

class TestStrategyComparison:

    def test_compare_strategies_returns_four(self):
        """Compare endpoint must return exactly 4 strategies."""
        r = client.post("/optimize/strategies", json={
            "crop_ids": ["onion", "wheat", "chickpea", "mustard"],
            "total_land_acres": 10.0,
            "water_available_kl": 16000.0,
            "fertilizer_available_kg": 1000.0,
            "total_budget_inr": 400000.0
        })
        assert r.status_code == 200
        strategies = r.json()["strategies"]
        assert len(strategies) == 4

    def test_compare_strategies_names_distinct(self):
        """Each strategy must have a distinct name."""
        r = client.post("/optimize/strategies", json={
            "crop_ids": ["onion", "wheat", "chickpea", "mustard"],
            "total_land_acres": 10.0,
            "water_available_kl": 16000.0,
            "fertilizer_available_kg": 1000.0,
            "total_budget_inr": 400000.0
        })
        strategies = r.json()["strategies"]
        names = [s["strategy"] for s in strategies]
        assert len(set(names)) == 4, f"Duplicate strategy names: {names}"

    def test_max_profit_has_highest_profit(self):
        """Max Profit strategy must produce >= profit of Balanced and Low Budget."""
        r = client.post("/optimize/strategies", json={
            "crop_ids": ["onion", "wheat", "chickpea", "mustard"],
            "total_land_acres": 10.0,
            "water_available_kl": 16000.0,
            "fertilizer_available_kg": 1000.0,
            "total_budget_inr": 400000.0
        })
        strategies = r.json()["strategies"]
        by_name = {s["strategy"].lower().replace(" ", "_"): s for s in strategies}

        if all(s["status"] == "Optimal" for s in strategies):
            max_p = by_name.get("max_profit", {}).get("expected_net_profit_inr", 0)
            balanced = by_name.get("balanced", {}).get("expected_net_profit_inr", 0)
            low_b = by_name.get("low_budget", {}).get("expected_net_profit_inr", 0)
            # Max profit should be >= others (with small tolerance for LP rounding)
            assert max_p >= balanced - 1.0, \
                f"max_profit ({max_p}) < balanced ({balanced})"
            assert max_p >= low_b - 1.0, \
                f"max_profit ({max_p}) < low_budget ({low_b})"

    def test_water_saver_uses_least_water(self):
        """Water Saver strategy must use <= water of Balanced and Max Profit."""
        r = client.post("/optimize/strategies", json={
            "crop_ids": ["onion", "wheat", "chickpea", "mustard"],
            "total_land_acres": 10.0,
            "water_available_kl": 16000.0,
            "fertilizer_available_kg": 1000.0,
            "total_budget_inr": 400000.0
        })
        strategies = r.json()["strategies"]
        by_name = {s["strategy"].lower().replace(" ", "_"): s for s in strategies}

        optimal = {k: v for k, v in by_name.items() if v["status"] == "Optimal"}
        if "water_saver" in optimal and "max_profit" in optimal:
            ws_water = optimal["water_saver"]["total_water_used_kl"]
            mp_water = optimal["max_profit"]["total_water_used_kl"]
            assert ws_water <= mp_water + 100.0, \
                f"water_saver uses more water ({ws_water}) than max_profit ({mp_water})"

    def test_low_budget_uses_least_cost(self):
        """Low Budget strategy must cost <= Balanced and Max Profit strategies."""
        r = client.post("/optimize/strategies", json={
            "crop_ids": ["onion", "wheat", "chickpea", "mustard"],
            "total_land_acres": 10.0,
            "water_available_kl": 16000.0,
            "fertilizer_available_kg": 1000.0,
            "total_budget_inr": 400000.0
        })
        strategies = r.json()["strategies"]
        by_name = {s["strategy"].lower().replace(" ", "_"): s for s in strategies}

        optimal = {k: v for k, v in by_name.items() if v["status"] == "Optimal"}
        if "low_budget" in optimal and "max_profit" in optimal:
            lb_cost = optimal["low_budget"]["total_budget_used_inr"]
            mp_cost = optimal["max_profit"]["total_budget_used_inr"]
            assert lb_cost <= mp_cost + 100.0, \
                f"low_budget costs more ({lb_cost}) than max_profit ({mp_cost})"

    def test_each_strategy_constraints_respected(self):
        """Every strategy must respect its own resource limits."""
        r = client.post("/optimize/strategies", json={
            "crop_ids": ["onion", "wheat", "chickpea", "mustard"],
            "total_land_acres": 10.0,
            "water_available_kl": 16000.0,
            "fertilizer_available_kg": 1000.0,
            "total_budget_inr": 400000.0
        })
        for s in r.json()["strategies"]:
            if s["status"] != "Optimal":
                continue
            name = s["strategy"]
            assert s["total_land_allocated_acres"] <= 10.0 + 0.01, f"{name}: land violation"
            assert s["total_water_used_kl"] <= 16000.0 + 1.0, f"{name}: water violation"
            assert s["total_fertilizer_used_kg"] <= 1000.0 + 0.5, f"{name}: fertilizer violation"
            assert s["total_budget_used_inr"] <= 400000.0 + 100.0, f"{name}: budget violation"


# ══════════════════════════════════════════════════════════════════════════════
# 6. ECONOMICS — UNIT CONVERSIONS AND LABELS
# ══════════════════════════════════════════════════════════════════════════════

class TestEconomicsUnitsLabels:

    def test_water_saved_percent_is_vs_pool_not_external(self):
        """water_saved_percent = (1 - used/available) × 100 — measured vs own pool."""
        r = client.post("/optimize/allocate", json={
            "crop_ids": ["chickpea", "mustard"],
            "total_land_acres": 5.0,
            "water_available_kl": 5000.0,
            "fertilizer_available_kg": 400.0,
            "total_budget_inr": 150000.0,
            "strategy": "water_saver"
        })
        d = r.json()
        if d["status"] != "Optimal":
            pytest.skip("Infeasible")
        expected_saved_pct = round(
            (1.0 - d["total_water_used_kl"] / d["total_water_available_kl"]) * 100, 1
        )
        assert abs(d["water_saved_percent"] - expected_saved_pct) < 0.5, (
            f"water_saved_percent {d['water_saved_percent']} ≠ formula {expected_saved_pct}"
        )

    def test_fertilizer_saved_percent_vs_pool(self):
        """fertilizer_saved_percent = (1 - used/available) × 100."""
        r = client.post("/optimize/allocate", json={
            "crop_ids": ["chickpea", "mustard", "wheat"],
            "total_land_acres": 5.0,
            "water_available_kl": 8000.0,
            "fertilizer_available_kg": 500.0,
            "total_budget_inr": 150000.0,
            "strategy": "balanced"
        })
        d = r.json()
        if d["status"] != "Optimal":
            pytest.skip("Infeasible")
        expected = round(
            (1.0 - d["total_fertilizer_used_kg"] / d["total_fertilizer_available_kg"]) * 100, 1
        )
        assert abs(d["fertilizer_saved_percent"] - expected) < 0.5

    def test_profit_vs_max_percent_is_bounded_0_100(self):
        """profit_increase_percent must be between 0 and ~100 (LP max)."""
        r = client.post("/optimize/allocate", json={
            "crop_ids": ["onion", "wheat", "chickpea", "mustard"],
            "total_land_acres": 10.0,
            "water_available_kl": 16000.0,
            "fertilizer_available_kg": 1000.0,
            "total_budget_inr": 400000.0,
            "strategy": "balanced"
        })
        d = r.json()
        if d["status"] != "Optimal":
            pytest.skip("Infeasible")
        pct = d["profit_increase_percent"]
        assert 0 <= pct <= 105.0, f"profit_increase_percent={pct} out of [0,105]"

    def test_budget_used_str_format(self):
        """budget_used_str must be formatted as ₹X.XXL or ₹X,XXX."""
        r = client.post("/optimize/allocate", json={
            "crop_ids": ["onion", "wheat"],
            "total_land_acres": 5.0,
            "water_available_kl": 8000.0,
            "fertilizer_available_kg": 500.0,
            "total_budget_inr": 200000.0,
            "strategy": "balanced"
        })
        d = r.json()
        if d["status"] != "Optimal":
            pytest.skip("Infeasible")
        s = d["budget_used_str"]
        assert s.startswith("₹"), f"budget_used_str should start with ₹: {s}"

    def test_expected_profit_str_format(self):
        """expected_profit_str must start with ₹."""
        r = client.post("/optimize/allocate", json={
            "crop_ids": ["onion", "chickpea"],
            "total_land_acres": 5.0,
            "water_available_kl": 8000.0,
            "fertilizer_available_kg": 500.0,
            "total_budget_inr": 200000.0,
            "strategy": "max_profit"
        })
        d = r.json()
        if d["status"] != "Optimal":
            pytest.skip("Infeasible")
        assert d["expected_profit_str"].startswith("₹")

    def test_crop_profit_margin_is_db_value(self):
        """profit_margin_percent in optimizer output = db crop's profit_margin_percent."""
        from backend.app.data.crop_database import CROPS_DATABASE
        r = client.post("/optimize/allocate", json={
            "crop_ids": ["onion", "chickpea"],
            "total_land_acres": 4.0,
            "water_available_kl": 8000.0,
            "fertilizer_available_kg": 400.0,
            "total_budget_inr": 200000.0,
            "strategy": "balanced"
        })
        d = r.json()
        if d["status"] != "Optimal":
            pytest.skip("Infeasible")
        for c in d["crops"]:
            db_crop = CROPS_DATABASE.get(c["crop_id"])
            if db_crop:
                assert abs(c["profit_margin_percent"] - db_crop.profit_margin_percent) < 0.1, (
                    f"{c['crop_id']}: margin {c['profit_margin_percent']} "
                    f"≠ db {db_crop.profit_margin_percent}"
                )


# ══════════════════════════════════════════════════════════════════════════════
# 7. AUTH AND SECURITY
# ══════════════════════════════════════════════════════════════════════════════

class TestAuthSecurity:

    def test_unauthenticated_me_returns_401(self):
        r = client.get("/auth/me")
        assert r.status_code == 401

    def test_unauthenticated_history_returns_401(self):
        r = client.get("/history/plans")
        assert r.status_code == 401

    def test_unauthenticated_history_post_returns_401(self):
        """Unauthenticated POST /history/plans with valid payload must return 401."""
        r = client.post("/history/plans", json={
            "season": "Rabi 2026-27",
            "strategy": "Balanced",
            "crops": [{"name": "Wheat", "acres": 5.0}],
            "profit": "\u20b94.00L",
            "waterSaved": "20%",
            "fertilizerSaved": "15%",
            "status": "Draft"
        })
        assert r.status_code == 401

    def test_wrong_password_returns_401(self):
        r = client.post("/auth/login", json={
            "email": "ramesh.patil@gmail.com", "password": "wrongpassword"
        })
        assert r.status_code == 401

    def test_authenticated_me_returns_user(self):
        headers = auth_headers()
        r = client.get("/auth/me", headers=headers)
        assert r.status_code == 200
        data = r.json()
        assert data["email"] == "ramesh.patil@gmail.com"

    def test_recommend_crops_no_auth_required(self):
        """Recommendations do not require auth (public endpoint)."""
        r = client.post("/recommend/crops", json={
            "n": 80, "p": 45, "k": 70, "ph": 7.2,
            "temperature": 22.0, "humidity": 60.0, "rainfall": 400.0,
            "season": "Rabi"
        })
        assert r.status_code == 200

    def test_optimize_no_auth_required(self):
        """Optimization does not require auth (public endpoint)."""
        r = client.post("/optimize/allocate", json={
            "crop_ids": ["wheat", "chickpea"],
            "total_land_acres": 5.0,
            "water_available_kl": 8000.0,
            "fertilizer_available_kg": 400.0,
            "total_budget_inr": 150000.0,
            "strategy": "balanced"
        })
        assert r.status_code == 200


# ══════════════════════════════════════════════════════════════════════════════
# 8. API FAILURES AND GRACEFUL DEGRADATION
# ══════════════════════════════════════════════════════════════════════════════

class TestAPIEdgeCases:

    def test_empty_crop_list_falls_back_to_defaults(self):
        """Empty crop list must not crash — should use default crops or warn."""
        r = client.post("/optimize/allocate", json={
            "crop_ids": [],
            "total_land_acres": 5.0,
            "water_available_kl": 8000.0,
            "fertilizer_available_kg": 400.0,
            "total_budget_inr": 150000.0,
            "strategy": "balanced"
        })
        # Should either return 422 (validation) or 200 with warning
        assert r.status_code in (200, 422)

    def test_mixed_valid_invalid_crop_ids(self):
        """Mix of valid+invalid crop IDs → valid ones used, invalid warned."""
        r = client.post("/optimize/allocate", json={
            "crop_ids": ["wheat", "chickpea", "martian_grain"],
            "total_land_acres": 5.0,
            "water_available_kl": 8000.0,
            "fertilizer_available_kg": 400.0,
            "total_budget_inr": 150000.0,
            "strategy": "balanced"
        })
        assert r.status_code == 200
        d = r.json()
        # Valid crops should still be optimized
        assert d["status"] in ("Optimal", "Infeasible")
        if d["status"] == "Optimal":
            assert d.get("warning"), "Should warn about unknown crop 'martian_grain'"

    def test_health_endpoint_always_available(self):
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "healthy"

    def test_root_endpoint_lists_endpoints(self):
        r = client.get("/")
        assert r.status_code == 200
        data = r.json()
        assert "endpoints" in data
        assert "recommend" in data["endpoints"]
        assert "predict" in data["endpoints"]
        assert "optimize" in data["endpoints"]

    def test_model_info_endpoint(self):
        r = client.get("/model-info")
        assert r.status_code == 200
        data = r.json()
        assert "models" in data
        assert "disclaimer" in data
        assert "SYNTHETIC" in data["disclaimer"].upper() or "synthetic" in data["disclaimer"].lower()

    def test_high_rainfall_extreme_input(self):
        """Extreme rainfall (5000mm) should not crash — return a prediction."""
        r = client.post("/predict/yield", json={
            "crop_id": "chickpea", "n": 40, "p": 60, "k": 40,
            "ph": 7.0, "temperature": 22.0, "rainfall": 5000.0
        })
        assert r.status_code == 200
        d = r.json()
        assert d["expected_yield_q_per_acre"] > 0

    def test_very_high_temperature_extreme_input(self):
        """Extreme temperature (48°C) should not crash."""
        r = client.post("/predict/yield", json={
            "crop_id": "sorghum", "n": 80, "p": 40, "k": 40,
            "ph": 7.0, "temperature": 48.0, "rainfall": 300.0
        })
        assert r.status_code == 200
        d = r.json()
        assert "expected_yield_q_per_acre" in d


# ══════════════════════════════════════════════════════════════════════════════
# 9. UI/API VALUE CONSISTENCY
# ══════════════════════════════════════════════════════════════════════════════

class TestUIAPIConsistency:
    """
    Verifies that key values the frontend reads from the API match
    what the optimizer actually computes. These tests simulate what
    the frontend components (stats-cards.tsx, team-content.tsx) display.
    """

    def test_stats_cards_water_unused_label_vs_api(self):
        """
        stats-cards.tsx shows water_saved_str as 'X% of pool unused'.
        Verify this is computed as (1 - used/available)*100.
        """
        r = client.post("/optimize/allocate", json={
            "crop_ids": ["onion", "wheat", "chickpea", "mustard"],
            "total_land_acres": 10.0,
            "water_available_kl": 16000.0,
            "fertilizer_available_kg": 1000.0,
            "total_budget_inr": 400000.0,
            "strategy": "balanced"
        })
        d = r.json()
        if d["status"] != "Optimal":
            pytest.skip("Infeasible")

        # The displayed value water_saved_str corresponds to (1 - used/available)
        water_unused_fraction = 1.0 - (d["total_water_used_kl"] / d["total_water_available_kl"])
        pct_display = int(round(water_unused_fraction * 100))
        # water_saved_str should be "{pct_display}%"
        assert d["water_saved_str"] == f"{pct_display}%" or \
               d["water_saved_str"] == f"{int(d['water_saved_percent'])}%", \
               f"water_saved_str={d['water_saved_str']} doesn't match pool-unused {pct_display}%"

    def test_stats_cards_profit_label_vs_api(self):
        """
        stats-cards.tsx shows profit_increase_percent as '% of LP maximum'.
        This must NOT be labeled as 'more than your usual plan'.
        """
        r = client.post("/optimize/allocate", json={
            "crop_ids": ["onion", "wheat", "chickpea", "mustard"],
            "total_land_acres": 10.0,
            "water_available_kl": 16000.0,
            "fertilizer_available_kg": 1000.0,
            "total_budget_inr": 400000.0,
            "strategy": "balanced"
        })
        d = r.json()
        if d["status"] != "Optimal":
            pytest.skip("Infeasible")

        # profit_increase_percent is profit as % of LP maximum — not vs hardcoded baseline
        pct = d["profit_increase_percent"]
        assert 0 < pct <= 105.0, f"profit_increase_percent={pct} out of expected range"
        # Also check it's profit_vs_max_percent (same value, aliased)
        assert d.get("profit_vs_max_percent") == pct

    def test_resources_page_buffer_reserve_computation(self):
        """
        team-content.tsx now shows bufferReserve = budgetAvail - budgetUsedInr.
        Verify API provides both fields.
        """
        r = client.post("/optimize/allocate", json={
            "crop_ids": ["onion", "wheat", "chickpea", "mustard"],
            "total_land_acres": 10.0,
            "water_available_kl": 16000.0,
            "fertilizer_available_kg": 1000.0,
            "total_budget_inr": 400000.0,
            "strategy": "balanced"
        })
        d = r.json()
        if d["status"] != "Optimal":
            pytest.skip("Infeasible")

        buffer = d["total_budget_available_inr"] - d["total_budget_used_inr"]
        assert buffer >= 0, "Budget used should not exceed available"
        # Verify the API fields exist for frontend to compute from
        assert "total_budget_available_inr" in d
        assert "total_budget_used_inr" in d

    def test_resources_page_pool_denominators_in_api(self):
        """
        team-content.tsx displays 'X / Y kL' — both values must be in API response.
        """
        r = client.post("/optimize/allocate", json={
            "crop_ids": ["onion", "wheat"],
            "total_land_acres": 5.0,
            "water_available_kl": 12000.0,
            "fertilizer_available_kg": 600.0,
            "total_budget_inr": 200000.0,
            "strategy": "balanced"
        })
        d = r.json()
        # All pool denominators must be present in API response
        required = [
            "total_water_used_kl", "total_water_available_kl",
            "total_fertilizer_used_kg", "total_fertilizer_available_kg",
            "total_budget_used_inr", "total_budget_available_inr",
            "total_land_allocated_acres", "total_land_available_acres",
        ]
        for field in required:
            assert field in d, f"Missing field: {field}"

    def test_crop_advisor_season_filtering_rabi(self):
        """Rabi season recommendations should include Rabi-appropriate crops."""
        r = client.post("/recommend/crops", json={
            "n": 80, "p": 45, "k": 70, "ph": 7.2,
            "temperature": 20.0, "humidity": 50.0, "rainfall": 200.0,
            "season": "Rabi", "top_k": 6
        })
        assert r.status_code == 200
        data = r.json()
        assert data["count"] > 0
        # All returned crops should have non-empty sow windows
        for c in data["crops"]:
            assert c["sow"], f"Missing sow window for {c['crop_id']}"

    def test_crop_advisor_season_filtering_kharif(self):
        """Kharif season with appropriate summer inputs."""
        r = client.post("/recommend/crops", json={
            "n": 80, "p": 40, "k": 60, "ph": 6.8,
            "temperature": 30.0, "humidity": 75.0, "rainfall": 800.0,
            "season": "Kharif", "top_k": 6
        })
        assert r.status_code == 200
        data = r.json()
        assert data["count"] > 0
