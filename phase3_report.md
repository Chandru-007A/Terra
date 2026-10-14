# Terra — Phase 3 End-to-End Agricultural Validation Report

**Date:** 2026-10-13 | **Tests:** 166 passed, 0 failed | **TypeScript:** 0 errors

---

## Defects Found & Fixed

### 🔴 Critical — Optimizer: Degenerate Near-Zero Allocation

| | Detail |
|---|---|
| **Bug** | LP optimizer returned `status: "Optimal"` with only 0.045 acres allocated (e.g. onion with 100 kL water). Agronomically meaningless but technically LP-feasible. |
| **Root cause** | No minimum viable area threshold — LP can satisfy water constraint by allocating near-zero acres. The post-rounding `if acres > 0.01` filter kept the tiny allocation in the crops list. |
| **Fix** | Added minimum viable allocation gate: if `total_allocated_acres < 0.1`, return `Infeasible` with message `"Allocation of only X acres is not agronomically viable"`. |
| **File** | `backend/app/optimizer/linear_programming.py` lines 213-226 |

### 🔴 High — Yield Prediction: No Input Validation

| | Detail |
|---|---|
| **Bug** | `YieldPredictionRequest` accepted negative NPK values (e.g. N=−10) and impossible pH values (e.g. pH=15). These were passed raw to the ML model. |
| **Fix** | Added Pydantic `ge`/`le` field constraints: N/P/K ∈ [0, 500], pH ∈ [3.5, 10.5], temperature ∈ [−5, 55]°C, rainfall ∈ [0, 10000]mm. Invalid inputs now return 422 with a clear validation error. |
| **File** | `backend/app/schemas/yield_pred.py` |

### 🟡 Medium — Frontend: Misleading Hardcoded Water Label

| | Detail |
|---|---|
| **Bug** | `team-content.tsx` displayed `"{waterSaved} saved vs flood irrigation"`. The `water_saved_str` field is computed as % of own pool unused (not vs flood irrigation baseline). |
| **Fix** | Changed to `"{waterSaved} of pool unused vs full allocation"`. |
| **File** | `frontend/components/dashboard/team/team-content.tsx` |

### 🟡 Medium — Frontend: Hardcoded Buffer Reserve

| | Detail |
|---|---|
| **Bug** | Buffer reserve displayed as hardcoded `"₹67,600 buffer reserve remaining"` and `"17% unspent budget"` regardless of actual allocation. |
| **Fix** | Now computed dynamically: `bufferReserve = total_budget_available_inr − total_budget_used_inr`; `bufferPct` shown as computed %. |
| **File** | `frontend/components/dashboard/team/team-content.tsx` |

### 🟡 Medium — Frontend: Hardcoded Resource Pool Denominators

| | Detail |
|---|---|
| **Bug** | Water, fertilizer, budget, and land pool sizes were hardcoded as `/ 16,000 kL`, `/ 1,000 kg`, `/ ₹4.00L`, `/ 10 Acres` in the Resources page. |
| **Fix** | All denominators now read from live API fields: `total_water_available_kl`, `total_fertilizer_available_kg`, `total_budget_available_inr`, `total_land_available_acres`. |
| **File** | `frontend/components/dashboard/team/team-content.tsx` |

### 🟡 Medium — Frontend: Misleading Fallback Stats Labels

| | Detail |
|---|---|
| **Bug** | Dashboard fallback `defaultStats` still showed `"17% more than your usual plan"` and `"4,700 kL less than usual"` when API is unreachable. These are arbitrary baselines, not real comparisons. |
| **Fix** | Updated to honest fallback text: `"Indicative — connect API for live result"`, `"of available pool unused — indicative"`. Water card title changed from `"Water Saved"` → `"Water Unused"`. |
| **File** | `frontend/components/dashboard/dashboard/stats-cards.tsx` |

---

## Verification Results

### Backend Tests: 166/166 Passed

```
python -m pytest backend/tests/ --tb=short -q
166 passed, 1 warning in 31.55s
```

| Test File | Tests | Focus |
|---|---|---|
| `test_regression.py` | 55 | Phase 1 fixes (auth, optimizer, ML, security) |
| `test_phase2.py` | 49 | Phase 2 data provenance, real data, CV eval |
| `test_phase3_e2e.py` | 62 | Phase 3 E2E workflow, constraints, economics |

### Phase 3 Test Coverage (62 tests)

| Class | Tests | Coverage |
|---|---|---|
| `TestCompleteWorkflow` | 12 | Login → recommend → optimize → profit/yield/cost math |
| `TestConstrainedFarms` | 6 | Water-, fertilizer-, land-, budget-constrained, tight multi-constraint |
| `TestInfeasibleInputs` | 8 | Zero budget, impossible water, unknown strategy/crop, negative N, bad pH |
| `TestPredictionOptimizerConsistency` | 4 | DB-to-optimizer yield/cost/profit unit parity |
| `TestStrategyComparison` | 6 | Max Profit ≥ Balanced profit, Water Saver ≤ others water, Low Budget ≤ others cost |
| `TestEconomicsUnitsLabels` | 6 | water_saved % formula, fertilizer_saved % formula, profit_vs_max range |
| `TestAuthSecurity` | 7 | Auth enforcement, public vs. protected endpoints |
| `TestAPIEdgeCases` | 8 | Mixed valid/invalid crops, extreme inputs, model-info, health |
| `TestUIAPIConsistency` | 5 | Water label formula, profit_vs_max, buffer reserve fields, pool denominators |

### Frontend TypeScript: 0 Errors
```
npx tsc --noEmit
(exit 0 — no errors)
```

### Browser UI Verification (6 pages)

| Page | Status | Notes |
|---|---|---|
| `/login` | ✅ | Two-column professional layout, auth works |
| `/dashboard` | ✅ | Stats cards show live LP data; "LP maximum" label correct; "Water Unused" correct |
| `/dashboard/resources` | ✅ | "of pool unused vs full allocation"; buffer reserve computed dynamically |
| `/dashboard/strategies` | ✅ | 4 distinct live strategies: Balanced ₹4.62L, Max Profit ₹5.33L, Water Saver ₹4.00L, Low Budget ₹3.46L |
| `/dashboard/crop-advisor` | ✅ | Live crop recommendations; season toggle works (Rabi → Kharif shows Cotton/Maize/Rice) |
| `/dashboard/history` | ✅ | Plans table visible |

---

## Workflow Consistency Verified

### Profit Formula (API-verified)
```
gross_revenue = expected_yield_q × market_price_per_q  ✅
profit        = gross_revenue − cultivation_cost        ✅
total_profit  = Σ (crop_acres × profit_per_acre)        ✅  (sum matches reported total < ₹1 tolerance)
total_budget  = Σ (crop_acres × cultivation_cost)       ✅  (sum matches reported total < ₹1 tolerance)
total_yield   = Σ (crop_acres × base_yield)             ✅  (sum matches reported total < 0.5 q tolerance)
```

### Resource Constraint Verification (all 4 strategies, all resources)
- Land: allocated ≤ available + 0.01 acres ✅
- Water: used ≤ available + 1.0 kL ✅  
- Fertilizer: used ≤ available + 0.5 kg ✅
- Budget: used ≤ available + ₹100 ✅

### Strategy Ordering (LP-correct)
- Max Profit profit ≥ Balanced profit ✅
- Water Saver water ≤ Max Profit water ✅  
- Low Budget cost ≤ Max Profit cost ✅

---

## Remaining Known Limitations

| Limitation | Impact | Status |
|---|---|---|
| ML models trained on synthetic data only | Yield predictions and suitability scores reflect ICAR agronomic ranges, not real farm outcomes. Clearly disclosed via `prediction_range_note`. | Documented |
| Market prices are static CACP 2024-25 MSP benchmarks | Not live Agmarknet prices. Profit forecasts reflect benchmark, not today's mandi price. | Documented |
| `±10%` confidence interval is a heuristic | Labeled `confidence_interval_95` for schema compat but is NOT a validated 95% CI. `prediction_range_note` makes this explicit. | Documented |
| History "Apply Plan" — plan save requires login | Anonymous users cannot save strategies; correct 401 returned. UX improvement (redirect to login) is future work. | Acceptable |
| NASA POWER weather used for 4 regional profiles only | Extrapolation for other districts uses nearest profile. Acceptable for MVP. | Acceptable |

