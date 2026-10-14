# TERRA Backend — AI-Based Crop & Resource Optimization

FastAPI backend for the TERRA AI-Based Crop and Agricultural Resource Optimization System.

---

## Architecture Overview

| Layer | Technology |
|---|---|
| **Frontend** | Next.js 16 on `http://localhost:3000` |
| **Backend** | FastAPI on `http://localhost:8000` |
| **Auth** | JWT (PBKDF2-SHA256 password hashing) |
| **ML Models** | Scikit-learn RandomForest (classifier) + GradientBoosting (regressor) |
| **Optimizer** | SciPy Linear Programming (`scipy.optimize.linprog`, HiGHS solver) |
| **Database** | SQLite default (PostgreSQL supported via `DATABASE_URL`) |
| **Communication** | REST/JSON |

---

## Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI entry point, CORS, lifespan, router mounting
│   ├── config.py            # Settings (Pydantic BaseSettings, .env)
│   ├── database.py          # SQLAlchemy engine & session dependency
│   ├── models/              # SQLAlchemy ORM models (User, Plan)
│   ├── schemas/             # Pydantic request/response schemas
│   │   ├── auth.py          # UserRegister, UserLogin, UserUpdate, TokenResponse
│   │   ├── crop.py          # CropRecommendationRequest/Response, CropItem
│   │   ├── yield_pred.py    # YieldPredictionRequest/Response
│   │   ├── optimizer.py     # AllocationRequest/Response, StrategyComparison
│   │   └── plan.py          # PlanCreate, PlanResponse
│   ├── routers/             # API routers (one file per domain)
│   │   ├── auth.py          # /auth/*
│   │   ├── recommend.py     # /recommend/*
│   │   ├── predict.py       # /predict/*
│   │   ├── optimize.py      # /optimize/*
│   │   ├── history.py       # /history/*
│   │   └── data.py          # /data/* (provenance, benchmarks, climate, evaluation)
│   ├── ml/                  # Machine learning modules
│   │   ├── crop_classifier.py   # RandomForest crop suitability classifier
│   │   ├── yield_regressor.py   # GradientBoosting yield regressor (per-crop)
│   │   ├── synthetic_datasets.py# Agronomic training data generators
│   │   └── model_registry.py    # Singleton caching & model persistence
│   ├── optimizer/
│   │   └── linear_programming.py# SciPy HiGHS LP (4 strategies)
│   ├── data/                # Agronomy knowledge base & data pipelines
│   │   ├── crop_database.py # 22 crop profiles (nutrients, water, economics)
│   │   ├── soil_data.py     # Indian soil types and nutrient defaults
│   │   ├── weather_data.py  # Seasonal agro-climatic defaults
│   │   ├── process_datasets.py  # Raw→processed data ingestion pipeline
│   │   └── real_data_pipeline.py# Dataset loaders, benchmarking, provenance
│   └── utils/
│       └── security.py      # Password hashing & JWT token validation
├── docs/
│   ├── API_DOCUMENTATION.md
│   └── OPTIMIZATION_MATHEMATICS.md
├── tests/                   # 192-test pytest suite (unit + integration + E2E)
│   ├── test_api.py
│   ├── test_models_and_optimizer.py
│   ├── test_phase2.py
│   ├── test_phase3_e2e.py
│   ├── test_regression.py
│   └── test_dataset_acquisition.py
├── requirements.txt
├── Dockerfile
├── .env.example
└── run.py
```

---

## API Endpoints

### Root & Health
| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/` | None | System info, version, endpoint index |
| `GET` | `/health` | None | Liveness probe |
| `GET` | `/model-info` | None | ML model metadata & provenance disclaimer |

### Authentication (`/auth`)
| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/auth/register` | None | Register new farmer account |
| `POST` | `/auth/login` | None | Login, return JWT bearer token |
| `GET` | `/auth/me` | Bearer | Get current user profile |
| `PATCH` | `/auth/me` | Bearer | Update profile (farm size, soil, language) |

### Crop Recommendation (`/recommend`)
| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/recommend/crops` | None | Predict suitable crops for given soil & weather |
| `GET` | `/recommend/crops` | None | List crop catalog with optional season filter |
| `GET` | `/recommend/crops/{crop_id}` | None | Detailed agronomic profile |

### Yield Prediction (`/predict`)
| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/predict/yield` | None | Expected yield (q/acre), heuristic range, economics |

### Resource Optimization (`/optimize`)
| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/optimize/allocate` | None | Optimal land/water/fertilizer/budget allocation (LP) |
| `POST` | `/optimize/strategies` | None | Compare 4 strategies side-by-side |

### Plan History (`/history`)
| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/history/plans` | Bearer | List user's saved seasonal plans |
| `POST` | `/history/plans` | Bearer | Save an optimized plan |
| `GET` | `/history/plans/{plan_id}` | Bearer | Get specific plan (own plans only) |
| `DELETE` | `/history/plans/{plan_id}` | Bearer | Delete a saved plan |

### Agricultural Datasets & Provenance (`/data`)
| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/data/provenance` | None | Full dataset provenance catalog |
| `GET` | `/data/benchmarks/{crop_id}` | None | Empirical district yield distribution (DES India) |
| `GET` | `/data/climate/{district_id}` | None | NASA POWER seasonal agro-climate profile |
| `GET` | `/data/evaluation/classifier` | None | Classifier CV metrics on Kaggle benchmark |
| `GET` | `/data/evaluation/regressor` | None | Regressor regional benchmarks vs district actuals |

---

## Quickstart

### Prerequisites

- Python 3.11+
- pip

### 1. Install dependencies

```bash
pip install -r backend/requirements.txt
```

### 2. Configure environment

```bash
cp backend/.env.example backend/.env
# Edit backend/.env and set JWT_SECRET to a strong random value before deploying
```

### 3. Run the backend

```bash
# From project root
python -m uvicorn backend.app.main:app --reload --port 8000
# Or via helper script
python backend/run.py
```

Interactive Swagger docs: `http://localhost:8000/docs`

### 4. Run the frontend

```bash
cd frontend
pnpm install
pnpm dev
```

Frontend: `http://localhost:3000`

**Demo account:** `ramesh.patil@gmail.com` / `terra123`

---

## Environment Variables

All variables are optional; defaults are provided for local development only.

| Variable | Default | Description |
|---|---|---|
| `APP_NAME` | `TERRA Agricultural Optimization API` | Application display name |
| `APP_VERSION` | `1.0.0` | API version string |
| `DEBUG` | `False` | Enable debug mode |
| `DATABASE_URL` | `sqlite:///./terra.db` | Database connection string |
| `JWT_SECRET` | *(insecure default)* | **MUST be overridden in production** |
| `JWT_ALGORITHM` | `HS256` | JWT signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `10080` (7 days) | Token lifetime |
| `CORS_ORIGINS` | localhost:3000, localhost:8000 | Allowed CORS origins |

> **Security warning:** The default `JWT_SECRET` is publicly known. Always override it with a strong random value in any deployed environment. The backend emits a `UserWarning` at startup if the default is detected outside `DEBUG=True`.

---

## Dataset Provenance

All datasets are publicly available under open licences. Synthetic and real data are strictly labelled separately.

### 1. Crop Recommendation Benchmark
- **File:** `data/raw/crop_recommendation.csv` → `data/processed/crop_suitability_real.csv`
- **Source:** Atharva Ingle, "Crop Recommendation Dataset", Kaggle, 2020
- **Licence:** Open Database Licence (ODbL) / Kaggle terms
- **Nature:** 2,200 rows × 22 crops × 100 balanced observations. Augmented precision-agriculture benchmark — NOT uncurated field plot telemetry.
- **Scope:** Used to evaluate the classifier's cluster-separability. High CV accuracy (≈99%) is structurally expected due to balanced cluster design, and does NOT represent real-world farm generalization.

### 2. Indian District Crop Production
- **File:** `data/raw/crop_production_india.csv` → `data/processed/india_district_crop_yield.csv`
- **Source:** Directorate of Economics and Statistics (DES), Ministry of Agriculture & Farmers Welfare, Government of India
- **Nature:** 246,091 raw rows → 122,427 after filtering (zero-production, zero-area, NaN, sub-1ha, physiological outliers dropped). Real regional aggregates.
- **Use:** Empirical yield benchmarks for 19 crops across Indian districts. Used strictly for regional macro-benchmarking, NOT farm-level predictive validation (ecological fallacy applies).

### 3. NASA POWER Agro-Climatology
- **File:** `data/raw/nasa_power_climatology_districts.json` → `data/processed/district_agroclimate_profiles.json`
- **Source:** NASA POWER Project, `https://power.larc.nasa.gov/`, CC BY 4.0
- **Nature:** Seasonal temperature, humidity, and rainfall profiles for 8 Indian districts.

### 4. ML Training Data (Synthetic)
- All ML models (classifier, regressor) are trained on **synthetic data** generated from ICAR/FAO agronomic principles. Clearly labelled with `is_synthetic=True` and `data_source="synthetic_icar_agronomic"`.

---

## Running Tests

```bash
# From project root
python -m pytest backend/tests/ -v
```

**Current result: 192 passed, 0 failed** (run time ~40s).

Test files:
| File | Tests | Coverage |
|---|---|---|
| `test_api.py` | 5 | Core API endpoints |
| `test_models_and_optimizer.py` | 5 | ML model training & optimization |
| `test_phase2.py` | ~40 | Real data integration |
| `test_phase3_e2e.py` | ~70 | End-to-end workflow |
| `test_regression.py` | ~46 | Optimizer constraints, auth, round-trip |
| `test_dataset_acquisition.py` | 26 | Dataset integrity & API provenance |

---

## Data Import Pipeline

```bash
# From project root — regenerates processed datasets from raw files
python -m backend.app.data.process_datasets
```

Outputs:
- `data/processed/india_district_crop_yield.csv` — cleaned district yield records
- `data/processed/crop_suitability_real.csv` — benchmark crop recommendation dataset
- `data/processed/district_agroclimate_profiles.json` — NASA POWER climate profiles
- `data/processed/dataset_provenance.json` — full provenance catalog

---

## Model Limitations & Known Constraints

1. **Synthetic ML training:** Both the crop classifier and yield regressor are trained entirely on synthetically generated data. They have NOT been validated on held-out real farm records. Predictions are indicative only.
2. **No real-farm validation:** High CV accuracy on the Kaggle benchmark reflects cluster separability in a balanced dataset, not generalization to real, noisy field data.
3. **Regional yield ≠ farm yield:** District aggregate yield statistics (DES India) lack field-level NPK/irrigation covariates. Using them to validate farm-level ML predictions commits the ecological fallacy. The system explicitly decouples these.
4. **Economics are estimates:** Market prices reflect GoI MSP 2024-25 benchmarks and Agmarknet typical prices. Do not treat as live market prices.
5. **Optimizer is LP (linear):** SciPy HiGHS solves a linear program with crop economic parameters. Real farm resource allocation involves nonlinear interactions not captured by the model.
6. **Default JWT secret:** Must be overridden in production via `JWT_SECRET` environment variable.
7. **SQLite default:** Suitable for development/demo. Use PostgreSQL for production.
8. **Plan ID security:** Plan access requires authentication; users can only access their own plans.

---

## Dockerfile

```bash
docker build -t terra-backend ./backend
docker run -p 8000:8000 -e JWT_SECRET=<strong-secret> terra-backend
```