# TERRA — AI-Based Crop and Agricultural Resource Optimization System

TERRA is an intelligent precision agriculture decision-support platform designed to empower farmers and agricultural planners. It combines machine learning for crop suitability and yield prediction with classical SciPy linear programming (HiGHS solver) for constrained multi-resource allocation (land, water, fertilizer, budget).

---

## 🌟 Key Features

- **🌾 AI Crop Suitability Recommendation:** Multi-factor suitability scoring based on soil nutrients ($N, P, K$, $\text{pH}$), ambient temperature, humidity, rainfall, and seasonal compatibility.
- **📈 Yield Prediction & Response Curves:** Gradient Boosting regression models calibrated with agronomic response curves (Liebig's Law of the Minimum & Mitscherlich-Baule principles).
- **⚖️ Classical Resource Optimization:** SciPy Linear Programming (`scipy.optimize.linprog` with the HiGHS solver) offering four distinct farmer allocation strategies:
  1. *Balanced* (multi-objective normalized profit, water, and cost)
  2. *Maximum Profit* (constrained revenue maximization)
  3. *Water Saver* (minimizing irrigation with guaranteed profit floor)
  4. *Low Budget* (minimizing upfront capital expenditure)
- **🌦️ Live Weather & Agronomic Alerts:** Integration with Open-Meteo for 7-day numerical forecasts, heat spike detection, heavy rainfall alarms, and preventive mitigation advice.
- **📅 Seasonal Calendar & Milestone Tracking:** Automated growth phase timelines, irrigation/fertilizer task tracking, and progress monitoring.
- **📊 Interactive Modern Dashboard:** Built with Next.js 16, Tailwind CSS, Radix UI, Lucide icons, and Recharts.

---

## 🏗️ Architecture & Technology Stack

| Layer | Technologies |
| :--- | :--- |
| **Frontend** | Next.js 16 (App Router, Turbopack), React 19, TypeScript, Tailwind CSS, Lucide Icons, Recharts |
| **Backend API** | FastAPI, Uvicorn, Pydantic v2 |
| **Machine Learning** | Scikit-learn (RandomForestClassifier, GradientBoostingRegressor), NumPy, Pandas |
| **Optimization** | SciPy Linear Programming (`scipy.optimize.linprog` / HiGHS Solver) |
| **Database & ORM** | SQLite / PostgreSQL via SQLAlchemy 2.0 |
| **Security & Auth** | JWT Authentication with PBKDF2-SHA256 password hashing |
| **External APIs** | Open-Meteo API (Live Weather & Geocoding), NASA POWER (Agroclimatology normals) |

---

## 📂 Repository Structure

```
Terra/
├── backend/                  # FastAPI Application
│   ├── app/
│   │   ├── config.py         # Pydantic Settings & environment configuration
│   │   ├── database.py       # SQLAlchemy engine & session management
│   │   ├── main.py           # Application entry point, CORS, routers
│   │   ├── data/             # Crop databases, climate profiles & data pipelines
│   │   ├── ml/               # Suitability classifier, yield regressor, registry
│   │   ├── models/           # SQLAlchemy database models (User, Field, Plan, Notification, Event)
│   │   ├── optimizer/        # Linear programming allocation solver (HiGHS)
│   │   ├── routers/          # Modular API endpoints (Auth, Crops, Fields, Optimizer, etc.)
│   │   ├── schemas/          # Pydantic request/response validation schemas
│   │   └── services/         # Weather alerts, reminder sync, and business logic
│   ├── tests/                # Comprehensive test suite (214 tests, 100% pass rate)
│   ├── requirements.txt      # Python dependencies
│   └── run.py                # Backend server launcher
├── frontend/                 # Next.js 16 Web Dashboard
│   ├── app/                  # App router pages (dashboard, crop-advisor, calendar, etc.)
│   ├── components/           # UI components, layout widgets, stats cards, dialogs
│   ├── lib/                  # API clients, authentication, and state contexts
│   └── package.json          # Node dependencies & scripts
├── data/                     # Agricultural Datasets
│   ├── raw/                  # Raw crop production, recommendation, and NASA POWER climate data
│   └── processed/            # Cleaned district yield benchmarks, suitability profiles & provenance
└── Final,terra_report.md     # Audit, test verification, and architectural report
```

---

## 🚀 Getting Started

### Prerequisites
- **Python 3.10+**
- **Node.js 18+** & **npm** / **pnpm**

### 1. Backend Setup & Run
```bash
cd backend
python -m pip install -r requirements.txt
python run.py
```
* The API will be available at: `http://localhost:8000`
* Interactive API Documentation (Swagger UI): `http://localhost:8000/docs`

### 2. Frontend Setup & Run
```bash
cd frontend
npm install
npm run dev
```
* The web application will be accessible at: `http://localhost:3000`

### 3. Demo Credentials
The application automatically seeds a demo user upon startup:
- **Email:** `ramesh.patil@gmail.com`
- **Password:** `terra123`

---

## 🧪 Testing

Execute the complete backend test suite:
```bash
python -m pytest backend/tests -v
```
All 214 tests cover unit, integration, authentication, optimization constraints, and regression edge cases.

---

## 📄 License
This project is licensed under the MIT License.
