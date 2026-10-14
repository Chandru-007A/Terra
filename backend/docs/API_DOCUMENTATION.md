# TERRA Backend API Documentation

Welcome to the TERRA Agricultural Optimization Backend API.

- **Base URL**: `http://localhost:8000`
- **Interactive Swagger Docs**: `http://localhost:8000/docs`
- **ReDoc Interactive Reference**: `http://localhost:8000/redoc`

---

## 1. Authentication Endpoints (`/auth`)

### Register Farmer
- **Method**: `POST`
- **Path**: `/auth/register`
- **Request Body**:
```json
{
  "name": "Ramesh Patil",
  "email": "ramesh.patil@gmail.com",
  "password": "terra123",
  "village": "Nashik"
}
```
- **Response** (`200 OK`):
```json
{
  "access_token": "<jwt-token>",
  "token_type": "bearer",
  "user": {
    "id": "user-...",
    "name": "Ramesh Patil",
    "email": "ramesh.patil@gmail.com",
    "village": "Nashik",
    "district": "Maharashtra",
    "farmSizeAcres": 10.0,
    "soilType": "Black cotton soil",
    "language": "English",
    "createdAt": "2026-10-11T..."
  }
}
```

### Login
- **Method**: `POST`
- **Path**: `/auth/login`
- **Request Body**:
```json
{
  "email": "ramesh.patil@gmail.com",
  "password": "terra123"
}
```
- **Response** (`200 OK`):
```json
{
  "access_token": "<jwt-token>",
  "token_type": "bearer",
  "user": { ... }
}
```

### Get Profile
- **Method**: `GET`
- **Path**: `/auth/me`
- **Headers**: `Authorization: Bearer <access_token>` (optional in demo mode)

### Update Profile
- **Method**: `PATCH`
- **Path**: `/auth/me`
- **Headers**: `Authorization: Bearer <access_token>`
- **Request Body**:
```json
{
  "name": "Ramesh Patil",
  "village": "Nashik",
  "district": "Maharashtra",
  "farmSizeAcres": 12.0,
  "soilType": "Black cotton soil",
  "language": "Marathi"
}
```

---

## 2. Crop Recommendation Endpoints (`/recommend`)

### Predict Suitable Crops
- **Method**: `POST`
- **Path**: `/recommend/crops`
- **Request Body**:
```json
{
  "n": 80.0,
  "p": 45.0,
  "k": 70.0,
  "ph": 7.2,
  "temperature": 22.0,
  "humidity": 60.0,
  "rainfall": 420.0,
  "season": "Rabi",
  "top_k": 6
}
```
- **Response** (`200 OK`):
```json
{
  "count": 6,
  "crops": [
    {
      "id": 1,
      "crop_id": "onion",
      "emoji": "🧅",
      "title": "Onion (Rabi)",
      "suitability": "92% Highly Suitable",
      "status": "in",
      "yield": "90 q/acre",
      "sow": "Oct 25 – Nov 15",
      "profit": "₹74,000/acre",
      "water": "High",
      "variant": "default",
      "expected_yield_q": 90.0,
      "expected_profit": 74000.0,
      "water_requirement_kl": 2200.0,
      "fertilizer_kg": 104.0,
      "cost_per_acre": 61000.0,
      "market_price_per_q": 1500.0,
      "key_advantages": ["High market demand", "Excellent profit margin"],
      "irrigation_advice": "Frequent light irrigations; withhold water 10-15 days before harvest."
    }
  ]
}
```

### List All Crops
- **Method**: `GET`
- **Path**: `/recommend/crops?season=Rabi`

### Get Single Crop Details
- **Method**: `GET`
- **Path**: `/recommend/crops/{crop_id}` (e.g. `/recommend/crops/onion`)

---

## 3. Yield Prediction Endpoints (`/predict`)

### Predict Expected Yield
- **Method**: `POST`
- **Path**: `/predict/yield`
- **Request Body**:
```json
{
  "crop_id": "onion",
  "n": 110.0,
  "p": 55.0,
  "k": 75.0,
  "ph": 6.8,
  "temperature": 20.0,
  "rainfall": 450.0,
  "water_available_kl": 2200.0,
  "fertilizer_applied_kg": 104.0
}
```
- **Response** (`200 OK`):
```json
{
  "crop_id": "onion",
  "crop_name": "Onion (Rabi)",
  "emoji": "🧅",
  "expected_yield_q_per_acre": 90.0,
  "confidence_interval_95": {
    "lower_q_per_acre": 81.0,
    "upper_q_per_acre": 99.0
  },
  "benchmark_yield_q_per_acre": 90.0,
  "yield_gap_percent": 0.0,
  "market_price_per_q": 1500.0,
  "gross_revenue_per_acre": 135000.0,
  "cultivation_cost_per_acre": 61000.0,
  "expected_profit_per_acre": 74000.0,
  "profit_margin_percent": 54.8,
  "water_required_kl_per_acre": 2200.0,
  "fertilizer_required_kg_per_acre": 104.0
}
```

---

## 4. Resource Optimization Endpoints (`/optimize`)

### Allocate Resources (Single Strategy)
- **Method**: `POST`
- **Path**: `/optimize/allocate`
- **Request Body**:
```json
{
  "crop_ids": ["onion", "wheat", "chickpea", "mustard"],
  "total_land_acres": 10.0,
  "water_available_kl": 16000.0,
  "fertilizer_available_kg": 1000.0,
  "total_budget_inr": 400000.0,
  "strategy": "balanced"
}
```
- **Response** (`200 OK`):
```json
{
  "strategy": "Balanced",
  "status": "Optimal",
  "total_land_allocated_acres": 10.0,
  "total_land_available_acres": 10.0,
  "total_water_used_kl": 14750.0,
  "total_water_available_kl": 16000.0,
  "water_saved_percent": 29.8,
  "water_saved_str": "29%",
  "total_fertilizer_used_kg": 778.0,
  "total_fertilizer_available_kg": 1000.0,
  "fertilizer_saved_percent": 29.3,
  "fertilizer_saved_str": "29%",
  "total_budget_used_inr": 294600.0,
  "total_budget_available_inr": 400000.0,
  "budget_used_str": "₹2.95L",
  "expected_total_production_q": 355.0,
  "expected_production_str": "355 q",
  "expected_net_profit_inr": 403700.0,
  "expected_profit_str": "₹4.04L",
  "profit_increase_percent": 17.0,
  "crops": [
    {
      "crop_id": "onion",
      "name": "Onion (Rabi)",
      "emoji": "🧅",
      "acres": 3.0,
      "expected_yield_q": 270.0,
      "expected_profit_inr": 222000.0,
      "formatted_profit": "₹2.22L",
      "water_used_kl": 6600.0,
      "cost_inr": 183000.0,
      "profit_margin_percent": 54.8,
      "status": "Recommended"
    },
    {
      "crop_id": "wheat",
      "name": "Wheat (Rabi)",
      "emoji": "🌾",
      "acres": 3.0,
      "expected_yield_q": 54.0,
      "expected_profit_inr": 69000.0,
      "formatted_profit": "₹69,000",
      "water_used_kl": 4800.0,
      "cost_inr": 55200.0,
      "profit_margin_percent": 55.6,
      "status": "Recommended"
    },
    {
      "crop_id": "chickpea",
      "name": "Chickpea (Gram)",
      "emoji": "🫘",
      "acres": 3.0,
      "expected_yield_q": 24.0,
      "expected_profit_inr": 91200.0,
      "formatted_profit": "₹91,200",
      "water_used_kl": 2850.0,
      "cost_inr": 40800.0,
      "profit_margin_percent": 69.1,
      "status": "Recommended"
    },
    {
      "crop_id": "mustard",
      "name": "Mustard (Rabi)",
      "emoji": "🌼",
      "acres": 1.0,
      "expected_yield_q": 7.0,
      "expected_profit_inr": 21500.0,
      "formatted_profit": "₹21,500",
      "water_used_kl": 850.0,
      "cost_inr": 15600.0,
      "profit_margin_percent": 57.9,
      "status": "Stable"
    }
  ],
  "constraints_summary": {
    "land_utilization_percent": 100.0,
    "water_utilization_percent": 92.2,
    "fertilizer_utilization_percent": 77.8,
    "budget_utilization_percent": 73.7
  }
}
```

### Compare All Strategies Side-by-Side
- **Method**: `POST`
- **Path**: `/optimize/strategies`
- **Request Body**:
```json
{
  "crop_ids": ["onion", "wheat", "chickpea", "mustard"],
  "total_land_acres": 10.0,
  "water_available_kl": 16000.0,
  "fertilizer_available_kg": 1000.0,
  "total_budget_inr": 400000.0
}
```
- **Returns**: Array of 4 allocation strategies (`Balanced`, `Max Profit`, `Water Saver`, `Low Budget`).

---

## 5. Plan History Endpoints (`/history`)

- `GET /history/plans`: List saved plans for farmer
- `POST /history/plans`: Save a plan
- `GET /history/plans/{plan_id}`: Retrieve plan
- `DELETE /history/plans/{plan_id}`: Delete plan
