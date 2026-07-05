# PMS Engine — Executive Release Portfolio (v1.0 Complete)

An institutional-grade portfolio construction, stock screening, and rating platform for the Indian equity market (Nifty 50 universe).

---

## 1. Project Overview
PMS Engine v1.0 is an advanced analytics platform designed for portfolio managers, equity research analysts, and institutional teams. It combines traditional technical indicators, decision-tree machine learning models, and deep temporal recurrent neural networks (GRU) to filter, score, rank, and allocate equity capital.

### Tech Stack
- **API Engine**: FastAPI (Python) - asynchronous, high-performance, strictly typed with Pydantic.
- **Client App**: React (Vite) - SPA featuring customized HSL-tailored CSS variables, animations, and charts.
- **In-Memory Store**: Pandas DataFrame with automatic hot-reloads via local file joins.

---

## 2. System Architecture
```
                                +-------------------+
                                |   Web Browser     |
                                |  (React Client)   |
                                +---------+---------+
                                          |
                                    HTTPS | JSON REST
                                          v
                                +---------+---------+
                                |  FastAPI Backend  |
                                |    (Uvicorn)      |
                                +---------+---------+
                                          |
                        +-----------------+-----------------+
                        |                                   |
                  Pandas| Join                               Pandas| Load
                        v                                   v
             +----------+----------+             +----------+----------+
             | gru_scanner_results |             | final_institutional |
             |       (.csv)        |             |    scanner (.csv)   |
             +---------------------+             +---------------------+
```

---

## 3. Data & Scoring Flow
1. **Load**: On startup (or POST `/api/refresh`), the backend loads `final_institutional_scanner.csv`.
2. **Merge**: Joins the actual model probability metrics (`GRU_HOLD`, `GRU_LONG`, `GRU_SHORT`) and `ReturnScore` from `gru_scanner_results.csv` on the `Symbol` column.
3. **Sort**: Orders all stocks by `CompositeScoreV2` descending.
4. **Rank**: Assigns sequential positions from 1 to 50.
5. **Enrich**:
   - Calculates Percentiles: $\text{Percentile} = (1 - (rank - 1)/49) \times 100$.
   - Assigns UniversePosition (Top Decile, Upper Quartile, Middle Quartile, Lower Quartile, Bottom Decile).
   - Flags PortfolioEligibility and ConvictionLevel.
6. **XAI Compilation**: Generates descriptions for each sub-score using actual numbers (no invented indicators) and compiles rating drivers sorted by absolute impact.
7. **Serialize**: Returns JSON payloads serialized via strict Pydantic schemas.

---

## 4. Rating & Portfolio Methodology

### Dynamic Rating Engine
Ratings are assigned using quantile-based boundaries on the 50-stock sorted universe:
- **STRONG BUY**: Top decile (Percentile $\ge 90\%$) $\rightarrow$ Ranks 1–5.
- **BUY**: Next 20% ($75\% \le$ Percentile $< 90\%$) $\rightarrow$ Ranks 6–15.
- **HOLD**: Middle 40% ($25\% \le$ Percentile $< 75\%$) $\rightarrow$ Ranks 16–35.
- **SELL**: Next 20% ($10\% \le$ Percentile $< 25\%$) $\rightarrow$ Ranks 36–45.
- **STRONG SELL**: Bottom decile (Percentile $< 10\%$) $\rightarrow$ Ranks 46–50.

### Conviction-Weighted Allocations
The portfolio construction engine selects only **STRONG BUY** and **BUY** stocks (15 stocks total). Capital is allocated dynamically based on conviction weights:
$$\text{Weight}_i = \frac{\text{CompositeScoreV2}_i}{\sum_{j \in \text{Buys}} \text{CompositeScoreV2}_j} \times 100$$
$$\text{Amount Allocated}_i = \text{Capital} \times \frac{\text{Weight}_i}{100}$$

---

## 5. Explainable AI (XAI) Framework
PMS Engine v1.0 implements a fully auditable and traceable XAI system:
- **Traceable Reasons**: Sub-score narratives explain *why* Technical, ML, GRU, and Return metrics are generated using mathematical brackets based strictly on actual values.
- **RatingDrivers**: An array of indicators showing their contribution level (Very High, High, Moderate, Low), impact status (positive, negative, neutral), and descriptions. The list is sorted by absolute value to highlight the most influential components first.
- **Institutional Insight**: A expressed analyst-style recommendation based on the combined scoring profiles.

---

## 6. Release & Freeze Status
- **Current Version**: v1.0
- **Status**: Production-Frozen Release. No new features, code changes, or model retrainings will be accepted into this release branch.
- **Validation**: 100% Pass rate on all automated and manual checks (refer to [PHASE11_VALIDATION_REPORT.md](file:///c:/Users/Pratham.Jindal/Downloads/PMS%20Engine/phase11/PHASE11_VALIDATION_REPORT.md)).
- **Frozen Specifications**: Documented in [PHASE11_FREEZE.md](file:///c:/Users/Pratham.Jindal/Downloads/PMS%20Engine/phase11/PHASE11_FREEZE.md).

---

## 7. Phase 12 Development Roadmap

The updated sequence of milestones for Phase 12 focuses on expanding real-time ingestion, automating updates, and exporting reports directly from our Explainable AI (XAI) outputs (detailed in [PHASE12_ROADMAP.md](file:///c:/Users/Pratham.Jindal/Downloads/PMS%20Engine/phase11/PHASE12_ROADMAP.md)):
1. **Phase 12A — Live Market Data Feed**: Connecting to the Yahoo Finance API (only) for real-time daily data ingestion, without broker-specific hooks.
2. **Phase 12B — Automated Scanner Refresh**: Background scheduling loop that triggers hot-reloads every 15 minutes during active NSE market hours (09:15 to 15:30 IST).
3. **Phase 12C — AI Research Report Generator**: HTML and PDF export facilities delivering stylized Stock, Portfolio, and Market analyst reports directly from the XAI model outputs.
4. **Phase 12D — Watchlists & Alerts**: SQLite database layer storing user watchlists, tracking changes in rating, and managing alert logs.
5. **Phase 12E — Deployment Stages**: Split into **12E.1 Dockerization** (containerizing API and client services) and **12E.2 Cloud Deployment** (hosting containers on AWS ECS or GCP Cloud Run).
