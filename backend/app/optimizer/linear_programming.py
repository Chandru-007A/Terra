"""
Classical Agricultural Resource Optimization using SciPy Linear Programming (HiGHS).
Solves optimal land, water, fertilizer, and capital budget allocation
across shortlisted crops under practical farm constraints and diverse farmer strategies.

NOTE: Crop economic parameters (water requirement, fertilizer, cost, yield, price)
are drawn from the TERRA crop database, calibrated against ICAR / Agmarknet published
benchmarks. All LP results are model outputs; actual farm outcomes will vary with local
soil conditions, weather, and market prices.
"""

from typing import List, Dict, Any, Optional
import numpy as np
from scipy.optimize import linprog
from backend.app.data.crop_database import CROPS_DATABASE, get_crop, CropProfile

VALID_STRATEGIES = {"balanced", "max_profit", "water_saver", "low_budget"}


def format_currency_lakhs(amount_inr: float) -> str:
    """Formats INR into farmer-friendly Lakhs (L) or thousands (k)."""
    if amount_inr >= 100000:
        return f"\u20b9{amount_inr / 100000:.2f}L"
    return f"\u20b9{int(amount_inr):,}"


class AgriculturalOptimizer:
    def __init__(self):
        pass

    def solve_allocation(
        self,
        crop_ids: List[str],
        total_land_acres: float = 10.0,
        water_available_kl: float = 16000.0,
        fertilizer_available_kg: float = 1000.0,
        total_budget_inr: float = 400000.0,
        strategy: str = "balanced",
        custom_bounds: Optional[Dict[str, Dict[str, float]]] = None
    ) -> Dict[str, Any]:
        """
        Solves LP for crop allocation. Variables: x_c = acres allocated to crop c.
        Returns status="Infeasible" with an error message when no feasible solution
        exists; never silently substitutes an arbitrary equal-acre allocation.
        """
        # --- Input validation ---
        if total_land_acres <= 0:
            return self._error_response(strategy, "total_land_acres must be positive",
                                        total_land_acres, water_available_kl,
                                        fertilizer_available_kg, total_budget_inr)
        if water_available_kl <= 0:
            return self._error_response(strategy, "water_available_kl must be positive",
                                        total_land_acres, water_available_kl,
                                        fertilizer_available_kg, total_budget_inr)
        if fertilizer_available_kg <= 0:
            return self._error_response(strategy, "fertilizer_available_kg must be positive",
                                        total_land_acres, water_available_kl,
                                        fertilizer_available_kg, total_budget_inr)
        if total_budget_inr <= 0:
            return self._error_response(strategy, "total_budget_inr must be positive",
                                        total_land_acres, water_available_kl,
                                        fertilizer_available_kg, total_budget_inr)

        # --- Strategy normalisation ---
        strategy_key = strategy.lower().replace("-", "_").replace(" ", "_")
        if strategy_key not in VALID_STRATEGIES:
            return self._error_response(
                strategy,
                f"Unknown strategy {repr(strategy)}. Valid values: {sorted(VALID_STRATEGIES)}",
                total_land_acres, water_available_kl,
                fertilizer_available_kg, total_budget_inr
            )

        # --- Crop resolution ---
        valid_crops: List[CropProfile] = []
        unknown_ids: List[str] = []
        for cid in crop_ids:
            c = get_crop(cid)
            if c:
                valid_crops.append(c)
            else:
                unknown_ids.append(cid)

        if not valid_crops:
            valid_crops = [
                CROPS_DATABASE["onion"],
                CROPS_DATABASE["wheat"],
                CROPS_DATABASE["chickpea"],
                CROPS_DATABASE["mustard"],
            ]
            unknown_note = (
                f"None of the provided crop IDs {crop_ids} were found. "
                "Using default Rabi crop set."
            )
        else:
            unknown_note = (
                f"Unknown crop IDs ignored: {unknown_ids}" if unknown_ids else ""
            )

        num_crops = len(valid_crops)

        # --- Economic vectors ---
        profits = np.array([c.expected_profit_per_acre for c in valid_crops])
        waters = np.array([c.water_requirement_kl for c in valid_crops])
        fertilizers = np.array([c.total_fertilizer_kg for c in valid_crops])
        costs = np.array([c.cultivation_cost_per_acre for c in valid_crops])
        yields = np.array([c.base_yield_quintals_per_acre for c in valid_crops])

        # --- Inequality constraints: A_ub * x <= b_ub ---
        A_ub = [np.ones(num_crops), waters, fertilizers, costs]
        b_ub = [total_land_acres, water_available_kl, fertilizer_available_kg, total_budget_inr]

        # --- Per-crop bounds ---
        bounds = []
        for c in valid_crops:
            if custom_bounds and c.id in custom_bounds:
                lb = custom_bounds[c.id].get("min_acres", 0.0)
                ub = custom_bounds[c.id].get("max_acres", total_land_acres)
            elif strategy_key == "balanced":
                # lb * num_crops must never exceed total_land_acres (LP-feasibility guarantee)
                max_lb = total_land_acres / num_crops * 0.5
                lb = min(max_lb, 1.0, total_land_acres / (num_crops * 2.0))
                ub = max(lb, min(total_land_acres * 0.45, 4.0))
            else:
                lb = 0.0
                ub = total_land_acres
            bounds.append((lb, ub))

        # --- Max-profit baseline (used for profit-floor constraints) ---
        res_max_profit = linprog(
            -profits, A_ub=A_ub, b_ub=b_ub,
            bounds=[(0.0, total_land_acres)] * num_crops, method="highs",
        )
        max_feasible_profit = -res_max_profit.fun if res_max_profit.success else 0.0

        # --- Strategy-specific LP ---
        if strategy_key == "max_profit":
            res = linprog(
                -profits, A_ub=A_ub, b_ub=b_ub,
                bounds=[(0.0, total_land_acres * 0.6) for _ in valid_crops],
                method="highs",
            )

        elif strategy_key == "water_saver":
            A_s, b_s = list(A_ub), list(b_ub)
            if max_feasible_profit > 0:
                A_s.append(-profits)
                b_s.append(-0.75 * max_feasible_profit)
            res = linprog(waters, A_ub=A_s, b_ub=b_s,
                          bounds=[(0.0, total_land_acres)] * num_crops, method="highs")

        elif strategy_key == "low_budget":
            A_s, b_s = list(A_ub), list(b_ub)
            if max_feasible_profit > 0:
                A_s.append(-profits)
                b_s.append(-0.65 * max_feasible_profit)
            res = linprog(costs, A_ub=A_s, b_ub=b_s,
                          bounds=[(0.0, total_land_acres)] * num_crops, method="highs")

        else:  # balanced
            max_p = np.max(profits) if np.max(profits) > 0 else 1.0
            max_w = np.max(waters) if np.max(waters) > 0 else 1.0
            max_c = np.max(costs) if np.max(costs) > 0 else 1.0
            norm_profit = profits / max_p
            norm_water = waters / max_w
            norm_cost = costs / max_c
            c_obj = -(norm_profit - 0.35 * norm_water - 0.15 * norm_cost)
            res = linprog(c_obj, A_ub=A_ub, b_ub=b_ub, bounds=bounds, method="highs")

        # --- Infeasibility: never silently substitute ---
        if not res.success or res.x is None:
            return self._error_response(
                strategy_key,
                (
                    f"No feasible allocation found for strategy={repr(strategy_key)}. "
                    "Resources may be too low, profit-floor constraints too tight, "
                    "or crop requirements exceed available land/water/fertilizer/budget."
                ),
                total_land_acres, water_available_kl,
                fertilizer_available_kg, total_budget_inr,
                unknown_note=unknown_note,
            )

        # --- Round and normalise ---
        alloc_acres = np.clip(np.round(res.x, 3), 0.0, None)
        total_allocated = float(np.sum(alloc_acres))
        if total_allocated > total_land_acres + 1e-6:
            alloc_acres = np.round(alloc_acres * (total_land_acres / total_allocated), 3)

        # --- Post-rounding constraint check ---
        actual_land = float(np.sum(alloc_acres))
        actual_water = float(np.sum(alloc_acres * waters))
        actual_fert = float(np.sum(alloc_acres * fertilizers))
        actual_cost = float(np.sum(alloc_acres * costs))
        violations = []
        if actual_land > total_land_acres + 0.01:
            violations.append(f"land ({actual_land:.2f} > {total_land_acres})")
        if actual_water > water_available_kl + 1.0:
            violations.append(f"water ({actual_water:.1f} > {water_available_kl})")
        if actual_fert > fertilizer_available_kg + 0.5:
            violations.append(f"fertilizer ({actual_fert:.1f} > {fertilizer_available_kg})")
        if actual_cost > total_budget_inr + 100:
            violations.append(f"budget ({actual_cost:.0f} > {total_budget_inr})")
        if violations:
            return self._error_response(
                strategy_key,
                "Post-rounding constraint violation(s): " + "; ".join(violations) + ".",
                total_land_acres, water_available_kl,
                fertilizer_available_kg, total_budget_inr,
                unknown_note=unknown_note,
            )

        actual_profit = float(np.sum(alloc_acres * profits))
        actual_production = float(np.sum(alloc_acres * yields))

        # Minimum viable allocation check: < 0.1 acre total is not agronomically useful
        if actual_land < 0.1:
            return self._error_response(
                strategy_key,
                (
                    f"Allocation of only {actual_land:.3f} acres is not agronomically viable. "
                    "Available resources (water, fertilizer, or budget) are too low "
                    "to support a meaningful crop area on this farm."
                ),
                total_land_acres, water_available_kl,
                fertilizer_available_kg, total_budget_inr,
                unknown_note=unknown_note,
            )


        # Savings vs. available limits (not hardcoded external baselines)
        water_saved_pct = max(0.0, round((1.0 - actual_water / water_available_kl) * 100.0, 1))
        fert_saved_pct = max(0.0, round((1.0 - actual_fert / fertilizer_available_kg) * 100.0, 1))
        profit_vs_max = round(
            (actual_profit / max_feasible_profit) * 100.0, 1
        ) if max_feasible_profit > 0 else 0.0

        # --- Crop breakdown ---
        crop_breakdown = []
        for i, c in enumerate(valid_crops):
            acres = round(float(alloc_acres[i]), 3)
            if acres > 0.01:
                crop_breakdown.append({
                    "crop_id": c.id,
                    "name": c.name,
                    "emoji": c.emoji,
                    "acres": acres,
                    "expected_yield_q": round(acres * c.base_yield_quintals_per_acre, 1),
                    "expected_profit_inr": round(acres * c.expected_profit_per_acre, 2),
                    "formatted_profit": format_currency_lakhs(acres * c.expected_profit_per_acre),
                    "water_used_kl": round(acres * c.water_requirement_kl, 1),
                    "cost_inr": round(acres * c.cultivation_cost_per_acre, 2),
                    "profit_margin_percent": c.profit_margin_percent,
                    "status": "Recommended" if acres >= 2.0 else "Stable",
                })
        crop_breakdown.sort(key=lambda x: x["acres"], reverse=True)

        result = {
            "strategy": strategy_key.replace("_", " ").title(),
            "status": "Optimal",
            "total_land_allocated_acres": round(actual_land, 3),
            "total_land_available_acres": total_land_acres,
            "total_water_used_kl": round(actual_water, 1),
            "total_water_available_kl": water_available_kl,
            "water_saved_percent": water_saved_pct,
            "water_saved_str": f"{int(water_saved_pct)}%",
            "total_fertilizer_used_kg": round(actual_fert, 1),
            "total_fertilizer_available_kg": fertilizer_available_kg,
            "fertilizer_saved_percent": fert_saved_pct,
            "fertilizer_saved_str": f"{int(fert_saved_pct)}%",
            "total_budget_used_inr": round(actual_cost, 2),
            "total_budget_available_inr": total_budget_inr,
            "budget_used_str": format_currency_lakhs(actual_cost),
            "expected_total_production_q": round(actual_production, 1),
            "expected_production_str": f"{round(actual_production, 1)} q",
            "expected_net_profit_inr": round(actual_profit, 2),
            "expected_profit_str": format_currency_lakhs(actual_profit),
            "profit_increase_percent": profit_vs_max,
            "profit_vs_max_percent": profit_vs_max,
            "crops": crop_breakdown,
            "constraints_summary": {
                "land_utilization_percent": round((actual_land / total_land_acres) * 100, 1),
                "water_utilization_percent": round((actual_water / water_available_kl) * 100, 1),
                "fertilizer_utilization_percent": round((actual_fert / fertilizer_available_kg) * 100, 1),
                "budget_utilization_percent": round((actual_cost / total_budget_inr) * 100, 1),
            },
        }
        if unknown_note:
            result["warning"] = unknown_note
        return result

    def _error_response(
        self,
        strategy: str,
        error_message: str,
        total_land_acres: float,
        water_available_kl: float,
        fertilizer_available_kg: float,
        total_budget_inr: float,
        unknown_note: str = "",
    ) -> Dict[str, Any]:
        """Returns a clearly-marked infeasible/error response; never silently substitutes."""
        result = {
            "strategy": strategy.replace("_", " ").title() if strategy else "Unknown",
            "status": "Infeasible",
            "error": error_message,
            "total_land_allocated_acres": 0.0,
            "total_land_available_acres": total_land_acres,
            "total_water_used_kl": 0.0,
            "total_water_available_kl": water_available_kl,
            "water_saved_percent": 0.0,
            "water_saved_str": "N/A",
            "total_fertilizer_used_kg": 0.0,
            "total_fertilizer_available_kg": fertilizer_available_kg,
            "fertilizer_saved_percent": 0.0,
            "fertilizer_saved_str": "N/A",
            "total_budget_used_inr": 0.0,
            "total_budget_available_inr": total_budget_inr,
            "budget_used_str": "N/A",
            "expected_total_production_q": 0.0,
            "expected_production_str": "N/A",
            "expected_net_profit_inr": 0.0,
            "expected_profit_str": "N/A",
            "profit_increase_percent": 0.0,
            "profit_vs_max_percent": 0.0,
            "crops": [],
            "constraints_summary": {
                "land_utilization_percent": 0.0,
                "water_utilization_percent": 0.0,
                "fertilizer_utilization_percent": 0.0,
                "budget_utilization_percent": 0.0,
            },
        }
        if unknown_note:
            result["warning"] = unknown_note
        return result

    def compare_strategies(
        self,
        crop_ids: List[str],
        total_land_acres: float = 10.0,
        water_available_kl: float = 16000.0,
        fertilizer_available_kg: float = 1000.0,
        total_budget_inr: float = 400000.0,
    ) -> List[Dict[str, Any]]:
        """
        Runs optimization across all 4 core strategies for side-by-side comparison.
        Each strategy result is independent; infeasibility in one does not block others.
        """
        strategies = ["balanced", "max_profit", "water_saver", "low_budget"]
        return [
            self.solve_allocation(
                crop_ids=crop_ids,
                total_land_acres=total_land_acres,
                water_available_kl=water_available_kl,
                fertilizer_available_kg=fertilizer_available_kg,
                total_budget_inr=total_budget_inr,
                strategy=strat,
            )
            for strat in strategies
        ]


optimizer = AgriculturalOptimizer()
