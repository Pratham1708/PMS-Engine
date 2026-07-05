# PMS Engine

## Institutional AI-Powered Portfolio Management & Stock Rating System

---

# Overview

PMS Engine is an institutional-style stock screening, rating, and portfolio construction platform developed for the Indian equity market.

The system analyzes Nifty 50 stocks using a combination of:

* Technical Analysis
* Machine Learning Models
* Deep Learning (GRU Networks)
* Portfolio Construction Algorithms
* Institutional Ranking Systems
* Confidence Scoring Frameworks

The objective of the project is to replicate the type of stock-rating workflow used by professional research desks, portfolio management services (PMS), hedge funds, and institutional investment firms.

Instead of relying on a single indicator, PMS Engine combines multiple independent decision engines and produces a final investment rating:

* STRONG BUY
* BUY
* HOLD
* SELL
* STRONG SELL

---

# Project Goal

The primary goal of PMS Engine is to answer:

> "If an institutional analyst had to evaluate the entire Nifty 50 universe today, which stocks deserve capital allocation and which should be avoided?"

The system converts raw market data into:

* Technical Scores
* Machine Learning Scores
* Deep Learning Scores
* Reliability Scores
* Composite Scores
* Institutional Ratings
* Portfolio Allocations

---

# Current Universe

Current coverage:

* Nifty 50 Stocks

Future expansion targets:

* Nifty Next 50
* Nifty 500
* US Equities
* ETFs
* Sector Indices

---

# Complete Development Journey

---

## Phase 1 — Data Collection

Objective:

Create a historical database containing market data for the entire Nifty 50 universe.

Implemented:

* Historical OHLCV collection
* Symbol management
* Dataset consolidation
* Storage architecture

Output:

Historical market database

---

## Phase 2 — Data Cleaning

Objective:

Ensure data consistency and remove anomalies.

Implemented:

* Missing value handling
* Duplicate removal
* Date alignment
* Stock-level validation

Output:

Clean institutional-grade dataset

---

## Phase 3 — Feature Engineering

Objective:

Transform raw price data into predictive features.

Implemented:

### Trend Features

* EMA20
* EMA50
* EMA200

### Momentum Features

* RSI14
* MACD
* MACD Histogram

### Relative Position Features

* Price_vs_EMA20
* Price_vs_EMA50
* Price_vs_EMA200

### Trend Structure Features

* EMA20_vs_EMA50
* EMA50_vs_EMA200

Output:

Machine-learning-ready feature dataset

---

## Phase 4 — Technical Analysis Engine

Objective:

Create a technical scoring system similar to institutional research frameworks.

Implemented:

### Trend Analysis

* Price trend evaluation
* Moving average alignment

### Momentum Analysis

* RSI scoring
* MACD scoring

### Composite Technical Score

Range:

-100 to +100

Output:

TechnicalScore

---

## Phase 5 — Signal Generation

Objective:

Convert technical scores into actionable signals.

Signals:

* BUY
* HOLD
* SELL

Output:

Initial screening engine

---

## Phase 6 — Random Forest Model

Objective:

Introduce machine learning into the decision process.

Implemented:

* Random Forest classifier
* Historical training
* Feature importance analysis
* Prediction framework

Output:

Machine learning predictions

---

## Phase 7 — XGBoost Model

Objective:

Improve predictive performance using gradient boosting.

Implemented:

* XGBoost training
* Hyperparameter tuning
* Model evaluation

Output:

Enhanced ML predictions

---

## Phase 8 — LightGBM Model

Objective:

Create an institutional ensemble framework.

Implemented:

* LightGBM model
* Ensemble integration
* Probability outputs

Output:

Institutional ML layer

---

## Phase 9 — Institutional Scanner

Objective:

Combine technical and machine learning outputs.

Implemented:

### Composite Scoring Engine

Inputs:

* Technical Score
* ML Score
* Reliability Score

Outputs:

* CompositeScore
* Signal
* Confidence

Result:

Institutional Scanner V1

---

## Phase 10A — GRU Dataset Preparation

Objective:

Prepare sequential data for deep learning.

Implemented:

Sequence Length:

30 Days

Features:

* Price_vs_EMA20
* Price_vs_EMA50
* Price_vs_EMA200
* EMA20_vs_EMA50
* EMA50_vs_EMA200
* RSI14
* MACD
* MACD_HIST

Output:

GRU training dataset

---

## Phase 10B — GRU Deep Learning Model

Objective:

Introduce temporal learning.

Implemented:

* GRU architecture
* Multi-class prediction
* HOLD/LONG/SHORT classification

Output:

Deep learning model

File:

models/gru_final.keras

---

## Phase 10C — GRU Integration

Objective:

Combine GRU with existing ML pipeline.

Implemented:

GRU Outputs:

* GRU_HOLD
* GRU_LONG
* GRU_SHORT

Generated:

GRUScore

Created:

HybridMLScore

Output:

Institutional Scanner V2

---

## Phase 10D — Portfolio Construction Engine

Objective:

Convert signals into capital allocations.

Implemented:

### Equal Weight Portfolio

### Score-Based Portfolio

### Investment Allocation

Outputs:

* Portfolio Weights
* Capital Allocation
* Portfolio Summary

---

## Phase 10E — Institutional Validation

Objective:

Create institutional ranking and dashboard systems.

Implemented:

### Five-Level Rating System

* STRONG BUY
* BUY
* HOLD
* SELL
* STRONG SELL

### Confidence Engine

Confidence range:

0-100

### Institutional Dashboard

Outputs:

* Rating distribution
* Opportunity rankings
* Portfolio diagnostics

---

# Final Model Architecture

Technical Engine
↓
Random Forest
↓
XGBoost
↓
LightGBM
↓
GRU Deep Learning
↓
HybridMLScore
↓
CompositeScoreV2
↓
Five-Level Rating Engine
↓
Confidence Engine
↓
Portfolio Construction Engine

---

# Current Production Output

Primary production file:

data/live/final_institutional_scanner.csv

This file serves as the single source of truth for all future applications.

Contains:

* Symbol
* FinalRating
* FrontendSignal
* Confidence
* TechnicalScore
* MLScore
* GRUScore
* CompositeScoreV2
* ReliabilityScore

---

# Current Rating Distribution

The production system generates:

* STRONG BUY
* BUY
* HOLD
* SELL
* STRONG SELL

using institutional ranking logic.

# Project Structure

The project is structured into a `backend` (FastAPI service) and a `frontend` (React + Vite client), alongside legacy prototyping scripts in the root `src/` folder.

```
phase11/
├── backend/
│   ├── app/
│   │   ├── lab/             # Core quantitative research and backtesting modules
│   │   │   ├── backtester.py              # Historical price backtester
│   │   │   ├── model_researcher.py        # ML evaluation, calibration, and stability tests
│   │   │   ├── recommendation_auditor.py  # Forward return audit calculations
│   │   │   ├── indicators.py              # Base technical indicator formulas
│   │   │   ├── regime_detector.py         # Nifty market regime classifier
│   │   │   └── ... (stress_tester.py, monte_carlo.py, position_sizer.py, etc.)
│   │   ├── routers/         # API Endpoint routers mapping URLs to logic
│   │   │   ├── lab_models.py              # ML model comparison endpoints
│   │   │   ├── lab_validation.py          # Recommendation accuracy endpoints
│   │   │   ├── lab_experiments.py         # General experiments manager endpoints
│   │   │   └── ... (dashboard.py, portfolio.py, health.py, lab_*.py)
│   │   ├── services/        # Service layer (yFinance feeds, DB setup, report exports)
│   │   │   ├── db.py                      # Base SQLite DB connections and settings
│   │   │   ├── json_response.py           # SafeJSONResponse handling NaN/Infinity values
│   │   │   └── ... (yfinance_feed.py, report_generator.py, etc.)
│   │   └── models/          # Pydantic schemas for data serialization
│   │       └── schemas.py
│   ├── data/                # Data files, including the primary SQLite database (pms_engine.db)
│   ├── main.py              # Entry point establishing the FastAPI app and applying SafeJSONResponse globally
│   ├── requirements.txt     # Python libraries and backend dependencies
│   └── verify_all_lab_features.py  # Backend integration verification test scripts
│
├── frontend/
│   ├── src/
│   │   ├── api/             # API communication layer (labApi.js connecting to FastAPI)
│   │   ├── pages/           # React dashboard components
│   │   │   ├── QuantLab/
│   │   │   │   ├── QuantLabHome.jsx             # Categorized quant lab landing dashboard
│   │   │   │   ├── RecommendationValidation.jsx # Matrix accuracy and audit panel
│   │   │   │   └── ...
│   │   │   └── ...
│   │   ├── components/      # Reusable client components
│   │   └── index.css        # Central CSS design system
│   ├── package.json         # Frontend configuration and npm modules
│   └── vite.config.js       # Vite development configuration
│
└── src/                     # Prototype source files and notebooks from previous phases (1-10)
```

---

# Getting Started

Follow these instructions to set up and run the PMS Engine locally.

## Prerequisites

Before starting, ensure you have the following installed:
* **Python**: v3.10+
* **Node.js**: v20.19+ or v22.12+ (LTS recommended)
* **npm**: (bundled with Node.js)

## Quick Start (Windows)

The repository provides automated startup scripts. To launch both the backend and frontend in separate console windows:

1. Copy `.env.example` in the root directory to `.env`.
2. Double-click the **`start_all.bat`** file in the root folder.
   - This script will automatically create the Python virtual environment (`venv`), upgrade `pip`, install backend dependencies from `requirements.txt`, install frontend Node modules, and launch both development servers.

---

## Manual Installation & Run

If you prefer to set up and run the components manually, follow these steps:

### 1. Backend Setup (FastAPI)

```bash
# Navigate to the backend folder
cd backend

# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Upgrade pip
python -m pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env

# Run the backend API server
python main.py
```

* The Backend API Docs will be live at: **http://localhost:8000/api/docs**

### 2. Frontend Setup (React + Vite)

```bash
# Navigate to the frontend folder
cd frontend

# Install Node modules
npm install

# Start the Vite development server
npm run dev
```

* The Frontend Dashboard will be live at: **http://localhost:5173**

---

# Technology Stack

Language:

* Python

Libraries:

* Pandas
* NumPy
* Scikit-Learn
* XGBoost
* LightGBM
* TensorFlow
* Keras

Development Environment:

* Jupyter Notebook

Future Environment:

* VS Code

---

# Future Roadmap

## Phase 11 (Completed)

Production Migration

* FastAPI Backend
* PostgreSQL Database
* API Architecture

## Phase 12 (Completed)

React Frontend

Features:

* Screener
* Dashboard
* Portfolio Builder
* Stock Detail Pages

## Phase 13

Live Market Integration

* Real-time data
* Automated scanner refresh
* Portfolio updates

## Phase 14

Production Deployment

* Vercel
* Railway
* Supabase

---

# Disclaimer

This project is intended for educational, research, and portfolio analytics purposes.

It does not constitute financial advice.

All investment decisions should be independently evaluated before capital deployment.

---

# Author

Pratham Jindal

B.Tech Student | Actuarial Science Candidate | AI & Quantitative Finance Enthusiast

Project Status:

Phase 12 Complete

Ready for Live Market Integration (Phase 13)
