# PMS Engine — Production Application

## Institutional AI-Powered Portfolio Management & Stock Rating System

---

## Architecture

```
phase11/
├── backend/                    # FastAPI Backend
│   ├── main.py                 # Application entry point
│   ├── requirements.txt        # Python dependencies
│   ├── .env.example            # Environment template
│   └── app/
│       ├── config.py           # Configuration (env vars)
│       ├── data/
│       │   └── loader.py       # CSV data loader (in-memory cache)
│       ├── models/
│       │   └── schemas.py      # Pydantic response models
│       ├── services/
│       │   ├── stock_service.py    # Stock query logic
│       │   └── portfolio_service.py # Portfolio construction
│       └── routers/
│           ├── health.py       # GET /api/health
│           ├── stocks.py       # GET /api/stocks, /stock/{symbol}, /top-buys, /top-sells
│           ├── dashboard.py    # GET /api/dashboard, /ratings-distribution, /scanner-summary, POST /refresh
│           └── portfolio.py    # GET /api/portfolio?capital=X
├── frontend/                   # React + Vite Frontend
│   ├── src/
│   │   ├── index.css           # Complete design system
│   │   ├── App.jsx             # Root component with routing
│   │   ├── main.jsx            # Vite entry point
│   │   ├── api/                # Axios API client
│   │   ├── components/         # Reusable components
│   │   │   ├── common/         # RatingBadge, ConfidenceBar, ScoreBar, StatCard, LoadingSpinner
│   │   │   └── layout/         # Sidebar, Header
│   │   └── pages/              # Dashboard, Screener, StockDetail, Portfolio, Ratings, SystemOverview
│   ├── package.json
│   └── index.html
├── final_institutional_scanner.csv   # Source of truth
├── models/                     # Trained ML models (not used in V1 API)
├── .env.example
└── README_PRODUCTION.md        # This file
```

---

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- npm 9+

### Backend Setup

```bash
cd phase11/backend

# Create virtual environment (optional but recommended)
python -m venv venv
venv\Scripts\activate     # Windows
# source venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Start the API server
uvicorn main:app --reload --port 8000
```

The API will be available at http://localhost:8000

API docs at http://localhost:8000/api/docs

### Frontend Setup

```bash
cd phase11/frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The frontend will be available at http://localhost:5173

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| GET | `/api/stocks` | All stocks (sortable, filterable, searchable) |
| GET | `/api/stock/{symbol}` | Single stock detail |
| GET | `/api/top-buys` | Top STRONG BUY + BUY stocks |
| GET | `/api/top-sells` | Top SELL + STRONG SELL stocks |
| GET | `/api/dashboard` | Dashboard aggregated metrics |
| GET | `/api/ratings-distribution` | Rating counts |
| GET | `/api/scanner-summary` | Universe summary stats |
| GET | `/api/portfolio?capital=X` | Portfolio allocation |
| POST | `/api/refresh` | Reload CSV without restart |

### Query Parameters

**GET /api/stocks**
- `sort_by` — Column to sort by (default: CompositeScoreV2)
- `order` — asc or desc (default: desc)
- `rating` — Filter by FinalRating
- `search` — Search symbol substring

**GET /api/portfolio**
- `capital` — Investment capital in INR (required)

---

## Rating System

| Rating | Criteria |
|--------|----------|
| STRONG BUY | CompositeScoreV2 ≥ 90th percentile |
| BUY | CompositeScoreV2 ≥ 70th percentile |
| HOLD | Between 30th and 70th percentile |
| SELL | CompositeScoreV2 ≤ 30th percentile |
| STRONG SELL | CompositeScoreV2 ≤ 10th percentile |

## Confidence Color Coding

| Range | Color |
|-------|-------|
| 80–100 | Green |
| 60–80 | Yellow |
| 0–60 | Red |

---

## Scoring Pipeline

1. **TechnicalScore** (-100 to +100) — EMA + RSI + MACD analysis
2. **MLScore** (-100 to +100) — Ensemble of RF + XGBoost + LightGBM
3. **GRUScore** (-100 to +100) — GRU deep learning on 30-day sequences
4. **HybridMLScore** — 60% MLScore + 40% GRUScore
5. **CompositeScoreV2** — 35% Technical + 30% HybridML + 20% ExpReturn + 15% Reliability
6. **FinalRating** — Quantile-based 5-level institutional rating
7. **Confidence** — abs(CompositeScore), capped at 100

---

## Data Source

**V1**: `final_institutional_scanner.csv` (in-memory, hot-reloadable)

The CSV contains 51 Nifty 50 stocks with columns:
- Symbol, FinalRating, Confidence, CompositeScoreV2
- TechnicalScore, MLScore, GRUScore, ReliabilityScore

---

## Future Expansion

The codebase is architected for future phases:

- **Phase 12**: PostgreSQL database (replace CSV loader with DB loader)
- **Phase 13**: JWT authentication
- **Phase 14**: Live market data integration (yfinance, Twelve Data)
- **Phase 15**: Cloud deployment (Vercel + Railway + Supabase)
- **Sector Data**: Sector field is present as a placeholder for future enrichment

---

## Technology Stack

- **Backend**: Python, FastAPI, Pandas, Pydantic
- **Frontend**: React 18, Vite, React Router, Axios, Recharts
- **ML Models**: scikit-learn, XGBoost, LightGBM, TensorFlow/Keras (pre-trained)

---

## Author

Pratham Jindal — B.Tech Student | Actuarial Science Candidate | AI & Quantitative Finance
