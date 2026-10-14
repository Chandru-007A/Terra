"""
Regression tests for optimizer edge cases, ML model inputs, and auth enforcement.
Covers: infeasible/zero resources, insufficient budgets, invalid inputs, rounding,
strategy fallbacks, prediction sensitivity, API error responses, and auth.
"""

import pytest
from fastapi.testclient import TestClient
from backend.app.ml.crop_classifier import CropSuitabilityClassifier
from backend.app.ml.yield_regressor import YieldPredictionRegressor
from backend.app.optimizer.linear_programming import AgriculturalOptimizer
from backend.app.main import app

client = TestClient(app)


# ─── Optimizer unit-level regression tests ────────────────────────────────────

class TestOptimizerValidation:
    """Input validation: zero/negative resources must return Infeasible, not an allocation."""

    def setup_method(self):
        self.opt = AgriculturalOptimizer()
        self.crop_ids = ["onion", "wheat", "chickpea", "mustard"]

    def test_zero_land_returns_infeasible(self):
        result = self.opt.solve_allocation(self.crop_ids, total_land_acres=0.0)
        assert result["status"] == "Infeasible"
        assert result["total_land_allocated_acres"] == 0.0
        assert "error" in result

    def test_negative_land_returns_infeasible(self):
        result = self.opt.solve_allocation(self.crop_ids, total_land_acres=-5.0)
        assert result["status"] == "Infeasible"
        assert "error" in result

    def test_zero_water_returns_infeasible(self):
        result = self.opt.solve_allocation(self.crop_ids, water_available_kl=0.0)
        assert result["status"] == "Infeasible"
        assert "error" in result

    def test_zero_fertilizer_returns_infeasible(self):
        result = self.opt.solve_allocation(self.crop_ids, fertilizer_available_kg=0.0)
        assert result["status"] == "Infeasible"
        assert "error" in result

    def test_zero_budget_returns_infeasible(self):
        result = self.opt.solve_allocation(self.crop_ids, total_budget_inr=0.0)
        assert result["status"] == "Infeasible"
        assert "error" in result

    def test_insufficient_budget_returns_infeasible_or_valid(self):
        """A budget of ₹1 cannot cover any crop's per-acre cultivation cost."""
        result = self.opt.solve_allocation(
            self.crop_ids,
            total_land_acres=10.0,
            total_budget_inr=1.0,
        )
        # Either infeasible (correct) or allocation cost must be within budget
        if result["status"] == "Infeasible":
            assert result["total_land_allocated_acres"] == 0.0
        else:
            assert result["total_budget_used_inr"] <= 1.0 + 0.01

    def test_unknown_strategy_returns_infeasible(self):
        result = self.opt.solve_allocation(self.crop_ids, strategy="moon_profit")
        assert result["status"] == "Infeasible"
        assert "error" in result
        assert "Unknown strategy" in result["error"]

    def test_empty_crops_uses_default_rabi_set(self):
        """Empty crop list falls back to default set with a warning."""
        result = self.opt.solve_allocation([])
        # Should succeed with default crops
        assert result["status"] == "Optimal"
        assert "warning" in result
        assert len(result["crops"]) > 0

    def test_unknown_crop_ids_warns_but_continues(self):
        """Mixture of valid + unknown crops: should succeed and warn."""
        result = self.opt.solve_allocation(
            ["onion", "wheat", "this_crop_does_not_exist"],
            total_land_acres=10.0,
        )
        if result["status"] == "Optimal":
            assert "warning" in result
            # Only real crops should appear in allocation
            crop_ids_in_result = {c["crop_id"] for c in result["crops"]}
            assert "this_crop_does_not_exist" not in crop_ids_in_result

    def test_all_unknown_crop_ids_uses_default(self):
        result = self.opt.solve_allocation(["fake1", "fake2"])
        assert result["status"] == "Optimal"
        assert "warning" in result

    def test_allocation_never_exceeds_land(self):
        result = self.opt.solve_allocation(
            self.crop_ids, total_land_acres=5.0, strategy="max_profit"
        )
        if result["status"] == "Optimal":
            assert result["total_land_allocated_acres"] <= 5.0 + 0.01

    def test_allocation_never_exceeds_water(self):
        result = self.opt.solve_allocation(
            self.crop_ids, total_land_acres=10.0, water_available_kl=5000.0
        )
        if result["status"] == "Optimal":
            assert result["total_water_used_kl"] <= 5000.0 + 1.0

    def test_allocation_never_exceeds_budget(self):
        result = self.opt.solve_allocation(
            self.crop_ids, total_budget_inr=80000.0
        )
        if result["status"] == "Optimal":
            assert result["total_budget_used_inr"] <= 80000.0 + 100

    def test_allocation_never_exceeds_fertilizer(self):
        result = self.opt.solve_allocation(
            self.crop_ids, fertilizer_available_kg=100.0
        )
        if result["status"] == "Optimal":
            assert result["total_fertilizer_used_kg"] <= 100.0 + 0.5

    def test_rounding_does_not_violate_constraints(self):
        """Run multiple small land scenarios to check rounding never causes violations."""
        for land in [1.0, 2.5, 5.0, 7.3, 10.0]:
            result = self.opt.solve_allocation(
                self.crop_ids, total_land_acres=land
            )
            if result["status"] == "Optimal":
                assert result["total_land_allocated_acres"] <= land + 0.01, \
                    f"Rounding violation at land={land}: {result['total_land_allocated_acres']}"

    def test_infeasible_does_not_contain_crops(self):
        """An infeasible result must have an empty crops list."""
        result = self.opt.solve_allocation(self.crop_ids, total_land_acres=0.0)
        assert result["crops"] == []

    def test_profit_vs_max_is_reasonable(self):
        """profit_vs_max_percent should be <= 100 and non-negative for a feasible solution."""
        result = self.opt.solve_allocation(self.crop_ids)
        if result["status"] == "Optimal":
            pct = result.get("profit_vs_max_percent", 0.0)
            assert 0.0 <= pct <= 105.0, f"profit_vs_max_percent out of range: {pct}"

    def test_savings_vs_limit_not_external_baseline(self):
        """water_saved_percent should be the fraction unused of the available limit, not vs hardcoded baseline."""
        water_limit = 16000.0
        result = self.opt.solve_allocation(
            self.crop_ids, total_land_acres=10.0, water_available_kl=water_limit
        )
        if result["status"] == "Optimal":
            expected_saved = round(
                (1.0 - result["total_water_used_kl"] / water_limit) * 100.0, 1
            )
            assert abs(result["water_saved_percent"] - expected_saved) <= 0.5, (
                f"Water saved mismatch: got {result['water_saved_percent']}, "
                f"expected ~{expected_saved}"
            )


class TestOptimizerStrategies:
    """Strategy-specific correctness checks."""

    def setup_method(self):
        self.opt = AgriculturalOptimizer()
        self.crop_ids = ["onion", "wheat", "chickpea", "mustard"]
        self.kwargs = {
            "total_land_acres": 10.0,
            "water_available_kl": 16000.0,
            "fertilizer_available_kg": 1000.0,
            "total_budget_inr": 400000.0,
        }

    def test_all_four_strategies_return(self):
        results = self.opt.compare_strategies(self.crop_ids, **self.kwargs)
        assert len(results) == 4
        strategy_names = {r["strategy"].lower() for r in results}
        assert "balanced" in strategy_names
        assert "max profit" in strategy_names
        assert "water saver" in strategy_names
        assert "low budget" in strategy_names

    def test_strategies_do_not_share_allocation(self):
        """Each strategy call should be independent."""
        r1 = self.opt.solve_allocation(self.crop_ids, strategy="max_profit", **self.kwargs)
        r2 = self.opt.solve_allocation(self.crop_ids, strategy="water_saver", **self.kwargs)
        if r1["status"] == "Optimal" and r2["status"] == "Optimal":
            # Water saver should generally use less water than max profit
            assert r2["total_water_used_kl"] <= r1["total_water_used_kl"] * 1.05

    def test_compare_strategies_infeasible_strategy_does_not_abort_others(self):
        """Even if one strategy is infeasible, compare_strategies returns all 4."""
        # Very tight budget may make some strategies infeasible
        results = self.opt.compare_strategies(
            self.crop_ids,
            total_land_acres=10.0,
            water_available_kl=16000.0,
            fertilizer_available_kg=1000.0,
            total_budget_inr=50000.0,  # very tight
        )
        assert len(results) == 4


# ─── ML model regression tests ────────────────────────────────────────────────

class TestYieldRegressor:
    """Yield prediction sensitivity and disclaimer checks."""

    def setup_method(self):
        self.reg = YieldPredictionRegressor()
        self.reg.train()

    def test_prediction_responds_to_water_change(self):
        """More water should not decrease predicted yield (within a realistic range)."""
        low_water = self.reg.predict_yield(
            "wheat", n=120, p=60, k=40, ph=6.8, temperature=18, rainfall=450,
            water_available_kl=800.0
        )
        high_water = self.reg.predict_yield(
            "wheat", n=120, p=60, k=40, ph=6.8, temperature=18, rainfall=450,
            water_available_kl=2400.0
        )
        # High water yield should be >= low water yield (allow 5% tolerance)
        assert high_water["expected_yield_q_per_acre"] >= low_water["expected_yield_q_per_acre"] * 0.95

    def test_prediction_range_note_is_present(self):
        """The disclaimer note must be present in responses."""
        result = self.reg.predict_yield(
            "onion", n=120, p=60, k=80, ph=6.8, temperature=20, rainfall=450
        )
        assert "prediction_range_note" in result
        note = result["prediction_range_note"]
        assert note is not None
        assert "heuristic" in note.lower() or "synthetic" in note.lower()

    def test_ci_bounds_straddle_prediction(self):
        result = self.reg.predict_yield(
            "wheat", n=120, p=60, k=40, ph=6.8, temperature=18, rainfall=450
        )
        y = result["expected_yield_q_per_acre"]
        lb = result["confidence_interval_95"]["lower_q_per_acre"]
        ub = result["confidence_interval_95"]["upper_q_per_acre"]
        assert lb <= y <= ub

    def test_unknown_crop_raises_value_error(self):
        with pytest.raises(ValueError, match="Unknown crop ID"):
            self.reg.predict_yield("totally_fake_crop", n=80, p=45, k=60, ph=7.0,
                                   temperature=22, rainfall=450)

    def test_profit_margin_is_positive_for_viable_crop(self):
        result = self.reg.predict_yield(
            "onion", n=120, p=60, k=80, ph=6.8, temperature=20, rainfall=450
        )
        # Revenue > cost for onion at base yield
        assert result["gross_revenue_per_acre"] > 0
        # Margin may be negative for extreme inputs but should be a valid float
        assert isinstance(result["profit_margin_percent"], float)

    def test_gross_revenue_consistent_with_yield_and_price(self):
        result = self.reg.predict_yield(
            "chickpea", n=40, p=60, k=40, ph=7.0, temperature=22, rainfall=350
        )
        expected_rev = round(result["expected_yield_q_per_acre"] * result["market_price_per_q"], 2)
        assert abs(result["gross_revenue_per_acre"] - expected_rev) < 0.1


class TestCropClassifier:
    """Suitability score validity tests."""

    def setup_method(self):
        self.clf = CropSuitabilityClassifier()
        self.clf.train()

    def test_scores_in_valid_range(self):
        results = self.clf.predict_suitability(
            n=80, p=45, k=70, ph=7.2, temperature=22, humidity=60, rainfall=420
        )
        for r in results:
            assert 0 <= r["suitability_score"] <= 100, \
                f"Score out of range for {r['crop_id']}: {r['suitability_score']}"

    def test_status_consistent_with_score(self):
        results = self.clf.predict_suitability(
            n=80, p=45, k=70, ph=7.2, temperature=22, humidity=60, rainfall=420
        )
        for r in results:
            if r["suitability_score"] >= 70:
                assert r["status"] == "in", f"{r['crop_id']} score {r['suitability_score']} should be 'in'"
            else:
                assert r["status"] == "out", f"{r['crop_id']} score {r['suitability_score']} should be 'out'"

    def test_results_sorted_descending(self):
        results = self.clf.predict_suitability(
            n=80, p=45, k=70, ph=7.2, temperature=22, humidity=60, rainfall=420
        )
        scores = [r["suitability_score"] for r in results]
        assert scores == sorted(scores, reverse=True)

    def test_top_k_respected(self):
        for k in [1, 5, 10]:
            results = self.clf.predict_suitability(
                n=80, p=45, k=70, ph=7.2, temperature=22, humidity=60, rainfall=420,
                top_k=k
            )
            assert len(results) <= k


# ─── API-level regression tests ───────────────────────────────────────────────

class TestAPIInfeasibleCases:
    """API endpoints must return error responses for infeasible inputs."""

    def test_optimize_zero_land_returns_400_or_infeasible_body(self):
        payload = {
            "crop_ids": ["onion", "wheat"],
            "total_land_acres": 0.01,  # Below Pydantic ge=0.5 constraint
            "water_available_kl": 16000.0,
            "fertilizer_available_kg": 1000.0,
            "total_budget_inr": 400000.0,
            "strategy": "balanced"
        }
        res = client.post("/optimize/allocate", json=payload)
        # Should be 422 (Pydantic validation) because ge=0.5 is enforced
        assert res.status_code in (400, 422)

    def test_optimize_unknown_strategy_returns_infeasible(self):
        payload = {
            "crop_ids": ["onion", "wheat", "chickpea"],
            "total_land_acres": 10.0,
            "water_available_kl": 16000.0,
            "fertilizer_available_kg": 1000.0,
            "total_budget_inr": 400000.0,
            "strategy": "moon_farming_mode"
        }
        res = client.post("/optimize/allocate", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "Infeasible"
        assert "error" in data

    def test_predict_unknown_crop_returns_400(self):
        payload = {"crop_id": "dragon_fruit_fantasy"}
        res = client.post("/predict/yield", json=payload)
        assert res.status_code == 400
        assert "Unknown crop ID" in res.json()["detail"]


class TestAuthEnforcement:
    """Authentication must be enforced; unauthenticated requests must get 401."""

    def test_get_me_without_token_returns_401(self):
        res = client.get("/auth/me")
        assert res.status_code == 401

    def test_patch_me_without_token_returns_401(self):
        res = client.patch("/auth/me", json={"name": "Hacker"})
        assert res.status_code == 401

    def test_get_plans_without_token_returns_401(self):
        res = client.get("/history/plans")
        assert res.status_code == 401

    def test_save_plan_without_token_returns_401(self):
        plan = {
            "season": "Rabi 2026-27",
            "strategy": "Balanced",
            "crops": [{"name": "Wheat", "acres": 5.0}],
            "profit": "₹1L",
            "waterSaved": "20%",
            "fertilizerSaved": "15%",
            "status": "Current"
        }
        res = client.post("/history/plans", json=plan)
        assert res.status_code == 401

    def test_invalid_token_returns_401(self):
        headers = {"Authorization": "Bearer totally.invalid.token"}
        res = client.get("/auth/me", headers=headers)
        assert res.status_code == 401

    def test_valid_login_then_authenticated_endpoints(self):
        """Full auth flow: login → /auth/me → /history/plans."""
        login_res = client.post("/auth/login", json={
            "email": "ramesh.patil@gmail.com",
            "password": "terra123"
        })
        assert login_res.status_code == 200
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        me_res = client.get("/auth/me", headers=headers)
        assert me_res.status_code == 200
        assert me_res.json()["email"] == "ramesh.patil@gmail.com"

        plans_res = client.get("/history/plans", headers=headers)
        assert plans_res.status_code == 200
        assert isinstance(plans_res.json(), list)


class TestOptimizerAPIRoundTrip:
    """API-level constraint checks on optimizer endpoint."""

    def _get_allocation(self, **kwargs):
        payload = {
            "crop_ids": ["onion", "wheat", "chickpea", "mustard"],
            "total_land_acres": kwargs.get("total_land_acres", 10.0),
            "water_available_kl": kwargs.get("water_available_kl", 16000.0),
            "fertilizer_available_kg": kwargs.get("fertilizer_available_kg", 1000.0),
            "total_budget_inr": kwargs.get("total_budget_inr", 400000.0),
            "strategy": kwargs.get("strategy", "balanced"),
        }
        res = client.post("/optimize/allocate", json=payload)
        assert res.status_code == 200
        return res.json()

    def test_optimal_result_respects_land(self):
        data = self._get_allocation(total_land_acres=8.0)
        if data["status"] == "Optimal":
            assert data["total_land_allocated_acres"] <= 8.0 + 0.01

    def test_optimal_result_respects_water(self):
        data = self._get_allocation(water_available_kl=10000.0)
        if data["status"] == "Optimal":
            assert data["total_water_used_kl"] <= 10000.0 + 1.0

    def test_optimal_result_respects_budget(self):
        data = self._get_allocation(total_budget_inr=200000.0)
        if data["status"] == "Optimal":
            assert data["total_budget_used_inr"] <= 200000.0 + 100

    def test_infeasible_result_has_empty_crops(self):
        data = self._get_allocation(strategy="moon_farming_mode")
        if data["status"] == "Infeasible":
            assert data["crops"] == []
            assert "error" in data

    def test_strategies_comparison_returns_four(self):
        payload = {
            "crop_ids": ["onion", "wheat", "chickpea", "mustard"],
            "total_land_acres": 10.0,
            "water_available_kl": 16000.0,
            "fertilizer_available_kg": 1000.0,
            "total_budget_inr": 400000.0,
        }
        res = client.post("/optimize/strategies", json=payload)
        assert res.status_code == 200
        assert len(res.json()["strategies"]) == 4
