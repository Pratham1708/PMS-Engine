# PMS Engine Architecture

## Data Layer

nifty50_master_dataset.csv

Contains:

- OHLCV
- Technical Indicators
- Feature Engineering
- FutureReturn Labels

---

## Technical Layer

TechnicalScore

Inputs:

- EMA20
- EMA50
- EMA200
- RSI14
- MACD
- MACD Histogram

Output:

TechnicalScore

Range:

-100 to 100

---

## Machine Learning Layer

Random Forest

XGBoost

LightGBM

Output:

MLScore

Range:

-100 to 100

---

## Deep Learning Layer

GRU

Input Shape:

(30, 8)

Features:

Price_vs_EMA20
Price_vs_EMA50
Price_vs_EMA200
EMA20_vs_EMA50
EMA50_vs_EMA200
RSI14
MACD
MACD_HIST

Output:

HOLD
LONG
SHORT

---

## Hybrid Layer

HybridMLScore

Combines:

MLScore
GRUScore

---

## Composite Engine

CompositeScoreV2

Combines:

TechnicalScore
HybridMLScore
ReliabilityScore

---

## Rating Engine

Strong Buy
Buy
Hold
Sell
Strong Sell

Quantile Based

---

## Confidence Engine

Range:

0-100

Production capped at 100

---

## Portfolio Engine

Input:

FinalRating

Portfolio:

Strong Buy + Buy

---

## Production Output

final_institutional_scanner.csv