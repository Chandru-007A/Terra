# Mathematical Formulation of Agricultural Resource Optimization

This document specifies the mathematical formulation implemented in the TERRA optimization engine.

---

## 1. Decision Variables

Let $C = \{1, 2, \dots, n\}$ be the set of shortlisted suitable crops.

For each crop $i \in C$, define the continuous decision variable:
$$x_i \ge 0$$
where $x_i$ represents the land area allocated to crop $i$ in **acres**.

---

## 2. Resource Parameters & Agronomic Data

For each crop $i \in C$:
- $P_i$: Expected net profit per acre ($\text{INR/acre}$)
- $W_i$: Irrigation water requirement per acre ($\text{kL/acre}$)
- $F_i$: Total fertilizer requirement per acre ($\text{kg/acre}$)
- $K_i$: Cultivation cost per acre ($\text{INR/acre}$)
- $Y_i$: Base yield per acre ($\text{quintals/acre}$)
- $L_i^{\min}, L_i^{\max}$: Lower and upper bounds for crop $i$ to prevent monoculture and ensure rotation

Farm-level resource constraints:
- $A_{\text{total}}$: Total available arable land (acres)
- $W_{\max}$: Total available irrigation water (kL)
- $F_{\max}$: Available chemical & organic fertilizer allowance (kg)
- $B_{\max}$: Total available working capital budget (INR)

---

## 3. Practical Agricultural Constraints

### Land Capacity Constraint
The sum of land allocated cannot exceed total arable land:
$$\sum_{i=1}^n x_i \le A_{\text{total}}$$

### Irrigation Water Constraint
Water consumption across crops must not exceed farm water availability:
$$\sum_{i=1}^n W_i \cdot x_i \le W_{\max}$$

### Fertilizer Constraint
Nutrient applications must respect soil sustainability and budget limits:
$$\sum_{i=1}^n F_i \cdot x_i \le F_{\max}$$

### Working Capital Budget Constraint
Total upfront cultivation expenditures cannot exceed available funds:
$$\sum_{i=1}^n K_i \cdot x_i \le B_{\max}$$

### Crop Diversity and Rotation Bounds
To avoid monoculture risk, market price collapse, and disease buildup:
$$L_i^{\min} \le x_i \le L_i^{\max}, \quad \forall i \in C$$

---

## 4. Optimization Strategies & Objective Functions

### Strategy 1: Maximum Profit (`max_profit`)
Maximizes aggregate farm profitability:
$$\max_{\mathbf{x}} \sum_{i=1}^n P_i \cdot x_i$$
Subject to all land, water, fertilizer, and budget constraints.

### Strategy 2: Water-Saving Optimization (`water_saver`)
Minimizes irrigation consumption while enforcing a minimum financial return floor:
$$\min_{\mathbf{x}} \sum_{i=1}^n W_i \cdot x_i$$
Subject to:
$$\sum_{i=1}^n P_i \cdot x_i \ge \theta_{\text{profit}} \cdot P_{\max}^*$$
where $P_{\max}^*$ is the maximum achievable profit and $\theta_{\text{profit}} = 0.75$ (75% floor).

### Strategy 3: Low-Budget Optimization (`low_budget`)
Minimizes total upfront cultivation expenditure while guaranteeing viable livelihood income:
$$\min_{\mathbf{x}} \sum_{i=1}^n K_i \cdot x_i$$
Subject to:
$$\sum_{i=1}^n P_i \cdot x_i \ge 0.65 \cdot P_{\max}^*$$

### Strategy 4: Balanced Diversified Strategy (`balanced`)
Multi-objective trade-off balancing income generation against water drawdown and cost risk:
$$\max_{\mathbf{x}} \sum_{i=1}^n \left( \frac{P_i}{\max_j P_j} - 0.35 \cdot \frac{W_i}{\max_j W_j} - 0.15 \cdot \frac{K_i}{\max_j K_j} \right) x_i$$
Subject to diversified crop acreage bounds.

---

## 5. Solver Implementation

Solved using `scipy.optimize.linprog` with the **HiGHS** simplex and interior-point dual solver (`method='highs'`), providing sub-15ms execution time on standard CPU hardware without external commercial solver licenses.
