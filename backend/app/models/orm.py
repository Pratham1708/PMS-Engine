from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Date,
    DateTime,
    BigInteger,
    ForeignKey,
    UniqueConstraint,
    Text,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

# ── Legacy & Admin Tables ──────────────────────────────────────────────────

class MyStock(Base):
    __tablename__ = "my_stocks"
    symbol = Column(String, primary_key=True)
    added_at = Column(String, nullable=False)


class AnalysisHistory(Base):
    __tablename__ = "analysis_history"
    analysis_id = Column(String, primary_key=True)
    symbol = Column(String, nullable=False)
    rating = Column(String, nullable=False)
    confidence = Column(Float, nullable=False)
    composite_score = Column(Float, nullable=False)
    analyzed_at = Column(String, nullable=False)


class ReportHistory(Base):
    __tablename__ = "report_history"
    report_id = Column(String, primary_key=True)
    report_type = Column(String, nullable=False)
    symbol = Column(String, nullable=True)
    generated_at = Column(String, nullable=False)
    analysis_id = Column(String, nullable=True)
    file_path = Column(String, nullable=False)
    report_version = Column(String, default="1.0")


# ── Lab Tables ─────────────────────────────────────────────────────────────

class LabExperiment(Base):
    __tablename__ = "lab_experiments"
    experiment_id = Column(String, primary_key=True)
    lab_module = Column(String, nullable=False)
    name = Column(String, nullable=False)
    symbol = Column(String, nullable=True)
    params_json = Column(String, nullable=True)
    version = Column(Integer, default=1)
    status = Column(String, default="pending")
    started_at = Column(String, nullable=True)
    completed_at = Column(String, nullable=True)
    error_msg = Column(String, nullable=True)
    reproducibility_seed = Column(Integer, default=42)
    engine_version = Column(String, nullable=True)
    dataset_version = Column(String, nullable=True)
    model_version = Column(String, nullable=True)
    indicator_version = Column(String, nullable=True)
    pipeline_stage = Column(String, default="Idea")
    is_paused = Column(Integer, default=0)


class LabMetric(Base):
    __tablename__ = "lab_metrics"
    id = Column(Integer, primary_key=True, autoincrement=True)
    experiment_id = Column(String, ForeignKey("lab_experiments.experiment_id"), nullable=False)
    metric_name = Column(String, nullable=False)
    metric_value = Column(Float, nullable=True)
    metric_str = Column(String, nullable=True)


class LabChart(Base):
    __tablename__ = "lab_charts"
    id = Column(Integer, primary_key=True, autoincrement=True)
    experiment_id = Column(String, ForeignKey("lab_experiments.experiment_id"), nullable=False)
    chart_type = Column(String, nullable=False)
    chart_data_json = Column(String, nullable=False)


class LabRecAudit(Base):
    __tablename__ = "lab_rec_audit"
    id = Column(Integer, primary_key=True, autoincrement=True)
    analysis_id = Column(String, nullable=False)
    symbol = Column(String, nullable=False)
    rating = Column(String, nullable=False)
    composite_score = Column(Float, nullable=True)
    analyzed_at = Column(String, nullable=False)
    horizon_days = Column(Integer, nullable=False)
    forward_return = Column(Float, nullable=True)
    validated = Column(Integer, nullable=True)
    validated_at = Column(String, nullable=True)
    __table_args__ = (
        UniqueConstraint("analysis_id", "horizon_days", name="uq_rec_audit_analysis_horizon"),
    )


class LabReport(Base):
    __tablename__ = "lab_reports"
    report_id = Column(String, primary_key=True)
    experiment_id = Column(String, nullable=True)
    report_type = Column(String, nullable=False)
    generated_at = Column(String, nullable=False)
    html_path = Column(String, nullable=False)
    pdf_path = Column(String, nullable=True)


class LabWeightSnapshot(Base):
    __tablename__ = "lab_weight_snapshots"
    id = Column(Integer, primary_key=True, autoincrement=True)
    experiment_id = Column(String, nullable=False)
    w_technical = Column(Float, nullable=True)
    w_ml = Column(Float, nullable=True)
    w_gru = Column(Float, nullable=True)
    w_reliability = Column(Float, nullable=True)
    target_metric = Column(String, nullable=True)
    metric_value = Column(Float, nullable=True)
    recorded_at = Column(String, nullable=True)


class LabDriftAlert(Base):
    __tablename__ = "lab_drift_alerts"
    id = Column(Integer, primary_key=True, autoincrement=True)
    alert_type = Column(String, nullable=False)
    metric_name = Column(String, nullable=False)
    threshold = Column(Float, nullable=True)
    current_value = Column(Float, nullable=True)
    message = Column(String, nullable=True)
    recorded_at = Column(String, nullable=True)


# ── Existing Snapshot Tables (SQLite Backward Compatibility) ───────────────

class Snapshot(Base):
    __tablename__ = "snapshots"
    snapshot_id = Column(String, primary_key=True)
    pipeline_run_id = Column(String, nullable=True)
    snapshot_date = Column(String, nullable=False)
    market_date = Column(String, nullable=False)
    generated_at = Column(String, nullable=False)
    is_official = Column(Integer, default=1)
    status = Column(String, default="generating")
    stocks_processed = Column(Integer, default=0)
    stocks_failed = Column(Integer, default=0)
    universe_version = Column(String, nullable=True)
    engine_version = Column(String, nullable=True)
    indicator_version = Column(String, nullable=True)
    scoring_version = Column(String, nullable=True)
    ml_model_version = Column(String, nullable=True)
    feature_version = Column(String, nullable=True)
    software_build = Column(String, nullable=True)
    pipeline_started_at = Column(String, nullable=True)
    pipeline_ended_at = Column(String, nullable=True)
    pipeline_duration_sec = Column(Float, nullable=True)
    validation_passed = Column(Integer, default=0)
    validation_score = Column(Float, nullable=True)
    published_at = Column(String, nullable=True)
    notes = Column(String, nullable=True)



class SnapshotStock(Base):
    __tablename__ = "snapshot_stock"
    id = Column(Integer, primary_key=True, autoincrement=True)
    snapshot_id = Column(String, ForeignKey("snapshots.snapshot_id", ondelete="CASCADE"), nullable=False)
    symbol = Column(String, nullable=False)
    company_name = Column(String, nullable=True)
    sector = Column(String, nullable=True)
    industry = Column(String, nullable=True)
    open = Column(Float, nullable=True)
    high = Column(Float, nullable=True)
    low = Column(Float, nullable=True)
    close = Column(Float, nullable=True)
    volume = Column(BigInteger, nullable=True)
    prev_close = Column(Float, nullable=True)
    daily_chg_pct = Column(Float, nullable=True)
    daily_chg_amt = Column(Float, nullable=True)
    week52_high = Column(Float, nullable=True)
    week52_low = Column(Float, nullable=True)
    technical_score = Column(Float, nullable=True)
    ml_score = Column(Float, nullable=True)
    gru_score = Column(Float, nullable=True)
    risk_score = Column(Float, nullable=True)
    momentum_score = Column(Float, nullable=True)
    trend_score = Column(Float, nullable=True)
    confidence = Column(Float, nullable=True)
    composite_score = Column(Float, nullable=True)
    reliability_score = Column(Float, nullable=True)
    final_rating = Column(String, nullable=True)
    portfolio_eligible = Column(Integer, nullable=True)
    conviction_level = Column(String, nullable=True)
    rank = Column(Integer, nullable=True)
    percentile = Column(Float, nullable=True)
    universe_position = Column(String, nullable=True)
    data_source = Column(String, nullable=True)
    download_status = Column(String, nullable=True)
    data_warnings = Column(String, nullable=True)
    __table_args__ = (
        UniqueConstraint("snapshot_id", "symbol", name="uq_snapshot_stock_symbol"),
    )


class LegacySnapshotIndicator(Base):
    __tablename__ = "snapshot_indicator"
    id = Column(Integer, primary_key=True, autoincrement=True)
    snapshot_id = Column(String, ForeignKey("snapshots.snapshot_id", ondelete="CASCADE"), nullable=False)
    symbol = Column(String, nullable=False)
    rsi_14 = Column(Float, nullable=True)
    ema_20 = Column(Float, nullable=True)
    ema_50 = Column(Float, nullable=True)
    ema_200 = Column(Float, nullable=True)
    macd = Column(Float, nullable=True)
    macd_signal = Column(Float, nullable=True)
    bb_upper = Column(Float, nullable=True)
    bb_lower = Column(Float, nullable=True)
    atr_14 = Column(Float, nullable=True)
    stoch_k = Column(Float, nullable=True)
    adx_14 = Column(Float, nullable=True)
    obv = Column(Float, nullable=True)
    vwap = Column(Float, nullable=True)
    above_ema20 = Column(Integer, nullable=True)
    above_ema50 = Column(Integer, nullable=True)
    above_ema200 = Column(Integer, nullable=True)
    near_52w_high = Column(Integer, nullable=True)
    near_52w_low = Column(Integer, nullable=True)
    __table_args__ = (
        UniqueConstraint("snapshot_id", "symbol", name="uq_snapshot_indicator_symbol"),
    )


class LegacySnapshotScore(Base):
    __tablename__ = "snapshot_score"
    id = Column(Integer, primary_key=True, autoincrement=True)
    snapshot_id = Column(String, ForeignKey("snapshots.snapshot_id", ondelete="CASCADE"), nullable=False)
    symbol = Column(String, nullable=False)
    trend_component = Column(Float, nullable=True)
    momentum_component = Column(Float, nullable=True)
    volatility_component = Column(Float, nullable=True)
    volume_component = Column(Float, nullable=True)
    lgbm_signal = Column(Float, nullable=True)
    rf_signal = Column(Float, nullable=True)
    xgb_signal = Column(Float, nullable=True)
    gru_hold = Column(Float, nullable=True)
    gru_long = Column(Float, nullable=True)
    gru_short = Column(Float, nullable=True)
    return_score = Column(Float, nullable=True)
    primary_driver = Column(String, nullable=True)
    secondary_driver = Column(String, nullable=True)
    w_technical = Column(Float, default=0.40)
    w_ml = Column(Float, default=0.35)
    w_gru = Column(Float, default=0.15)
    w_reliability = Column(Float, default=0.10)
    __table_args__ = (
        UniqueConstraint("snapshot_id", "symbol", name="uq_snapshot_score_symbol"),
    )


class SnapshotSector(Base):
    __tablename__ = "snapshot_sector"
    id = Column(Integer, primary_key=True, autoincrement=True)
    snapshot_id = Column(String, ForeignKey("snapshots.snapshot_id", ondelete="CASCADE"), nullable=False)
    sector = Column(String, nullable=False)
    stock_count = Column(Integer, nullable=True)
    avg_composite = Column(Float, nullable=True)
    avg_confidence = Column(Float, nullable=True)
    avg_technical = Column(Float, nullable=True)
    avg_momentum = Column(Float, nullable=True)
    avg_trend = Column(Float, nullable=True)
    avg_risk = Column(Float, nullable=True)
    strong_buy_count = Column(Integer, nullable=True)
    buy_count = Column(Integer, nullable=True)
    hold_count = Column(Integer, nullable=True)
    sell_count = Column(Integer, nullable=True)
    strong_sell_count = Column(Integer, nullable=True)
    bullish_pct = Column(Float, nullable=True)
    bearish_pct = Column(Float, nullable=True)
    sector_rank = Column(Integer, nullable=True)
    top_stock = Column(String, nullable=True)
    weakest_stock = Column(String, nullable=True)
    avg_daily_chg_pct = Column(Float, nullable=True)
    __table_args__ = (
        UniqueConstraint("snapshot_id", "sector", name="uq_snapshot_sector_name"),
    )


class SnapshotMarket(Base):
    __tablename__ = "snapshot_market"
    id = Column(Integer, primary_key=True, autoincrement=True)
    snapshot_id = Column(String, ForeignKey("snapshots.snapshot_id", ondelete="CASCADE"), nullable=False)
    total_stocks = Column(Integer, nullable=True)
    advancing_stocks = Column(Integer, nullable=True)
    declining_stocks = Column(Integer, nullable=True)
    unchanged_stocks = Column(Integer, nullable=True)
    advance_decline_ratio = Column(Float, nullable=True)
    advance_volume = Column(BigInteger, nullable=True)
    decline_volume = Column(BigInteger, nullable=True)
    stocks_above_ema20 = Column(Integer, nullable=True)
    stocks_above_ema50 = Column(Integer, nullable=True)
    stocks_above_ema200 = Column(Integer, nullable=True)
    pct_above_ema20 = Column(Float, nullable=True)
    pct_above_ema50 = Column(Float, nullable=True)
    pct_above_ema200 = Column(Float, nullable=True)
    week52_high_count = Column(Integer, nullable=True)
    week52_low_count = Column(Integer, nullable=True)
    avg_composite = Column(Float, nullable=True)
    avg_confidence = Column(Float, nullable=True)
    avg_rsi = Column(Float, nullable=True)
    avg_momentum = Column(Float, nullable=True)
    avg_daily_chg_pct = Column(Float, nullable=True)
    bullish_pct = Column(Float, nullable=True)
    bearish_pct = Column(Float, nullable=True)
    market_regime = Column(String, nullable=True)
    strong_buy_count = Column(Integer, nullable=True)
    buy_count = Column(Integer, nullable=True)
    hold_count = Column(Integer, nullable=True)
    sell_count = Column(Integer, nullable=True)
    strong_sell_count = Column(Integer, nullable=True)
    india_vix = Column(Float, nullable=True)
    pcr = Column(Float, nullable=True)
    fii_activity = Column(Float, nullable=True)
    dii_activity = Column(Float, nullable=True)
    __table_args__ = (
        UniqueConstraint("snapshot_id", name="uq_snapshot_market_snap"),
    )


class SnapshotWatchlist(Base):
    __tablename__ = "snapshot_watchlist"
    id = Column(Integer, primary_key=True, autoincrement=True)
    snapshot_id = Column(String, ForeignKey("snapshots.snapshot_id", ondelete="CASCADE"), nullable=False)
    watchlist_name = Column(String, nullable=False)
    symbol = Column(String, nullable=False)
    rank_in_list = Column(Integer, nullable=True)
    score_used = Column(Float, nullable=True)
    reason = Column(String, nullable=True)
    __table_args__ = (
        UniqueConstraint("snapshot_id", "watchlist_name", "symbol", name="uq_snapshot_watchlist_entry"),
    )


class SnapshotChange(Base):
    __tablename__ = "snapshot_change"
    id = Column(Integer, primary_key=True, autoincrement=True)
    snapshot_id = Column(String, ForeignKey("snapshots.snapshot_id", ondelete="CASCADE"), nullable=False)
    prev_snapshot_id = Column(String, nullable=True)
    symbol = Column(String, nullable=False)
    change_type = Column(String, nullable=False)
    prev_rating = Column(String, nullable=True)
    new_rating = Column(String, nullable=True)
    composite_diff = Column(Float, nullable=True)
    confidence_diff = Column(Float, nullable=True)
    technical_diff = Column(Float, nullable=True)
    ml_diff = Column(Float, nullable=True)
    momentum_diff = Column(Float, nullable=True)
    trend_diff = Column(Float, nullable=True)
    risk_diff = Column(Float, nullable=True)
    primary_driver = Column(String, nullable=True)
    secondary_driver = Column(String, nullable=True)
    is_significant = Column(Integer, default=0)


class SnapshotReport(Base):
    __tablename__ = "snapshot_report"
    id = Column(Integer, primary_key=True, autoincrement=True)
    snapshot_id = Column(String, ForeignKey("snapshots.snapshot_id", ondelete="CASCADE"), nullable=False)
    report_type = Column(String, nullable=False)
    symbol = Column(String, nullable=True)
    html_path = Column(String, nullable=True)
    pdf_path = Column(String, nullable=True)
    generated_at = Column(String, nullable=True)
    file_size_kb = Column(Float, nullable=True)


class SnapshotValidation(Base):
    __tablename__ = "snapshot_validation"
    id = Column(Integer, primary_key=True, autoincrement=True)
    snapshot_id = Column(String, ForeignKey("snapshots.snapshot_id", ondelete="CASCADE"), nullable=False)
    check_name = Column(String, nullable=False)
    status = Column(String, nullable=True)
    detail = Column(String, nullable=True)
    affected_count = Column(Integer, nullable=True)
    threshold = Column(Float, nullable=True)
    actual_value = Column(Float, nullable=True)


class SnapshotMetadata(Base):
    __tablename__ = "snapshot_metadata"
    id = Column(Integer, primary_key=True, autoincrement=True)
    snapshot_id = Column(String, ForeignKey("snapshots.snapshot_id", ondelete="CASCADE"), nullable=False)
    stage_name = Column(String, nullable=False)
    stage_status = Column(String, nullable=True)
    started_at = Column(String, nullable=True)
    completed_at = Column(String, nullable=True)
    duration_sec = Column(Float, nullable=True)
    stocks_success = Column(Integer, default=0)
    stocks_failed = Column(Integer, default=0)
    warnings_count = Column(Integer, default=0)
    errors_count = Column(Integer, default=0)
    log_summary = Column(String, nullable=True)


# ── Phase 13A Normalized Production Tables ─────────────────────────────────

class SecurityMaster(Base):
    __tablename__ = "security_master"
    symbol = Column(String, primary_key=True)
    exchange = Column(String, nullable=True, default="NSE")
    company_name = Column(String, nullable=False)
    sector = Column(String, nullable=True, default="—")
    industry = Column(String, nullable=True, default="—")
    isin = Column(String, nullable=True)
    market_cap_category = Column(String, nullable=True)


class MarketDaily(Base):
    __tablename__ = "market_daily"
    symbol = Column(String, primary_key=True)
    trading_date = Column(String, primary_key=True)  # YYYY-MM-DD
    open = Column(Float, nullable=True)
    high = Column(Float, nullable=True)
    low = Column(Float, nullable=True)
    close = Column(Float, nullable=True)
    adjusted_close = Column(Float, nullable=True)
    volume = Column(BigInteger, nullable=True)
    delivery_volume = Column(Float, nullable=True)
    vwap = Column(Float, nullable=True)
    previous_close = Column(Float, nullable=True)
    last_trading_date = Column(String, nullable=True)


class IndicatorSnapshot(Base):
    __tablename__ = "indicator_snapshot"
    id = Column(Integer, primary_key=True, autoincrement=True)
    snapshot_id = Column(String, nullable=False)
    symbol = Column(String, nullable=False)
    ema20 = Column(Float, nullable=True)
    ema50 = Column(Float, nullable=True)
    ema200 = Column(Float, nullable=True)
    sma20 = Column(Float, nullable=True)
    sma50 = Column(Float, nullable=True)
    rsi = Column(Float, nullable=True)
    macd = Column(Float, nullable=True)
    macd_signal = Column(Float, nullable=True)
    adx = Column(Float, nullable=True)
    atr = Column(Float, nullable=True)
    bb_upper = Column(Float, nullable=True)
    bb_lower = Column(Float, nullable=True)
    supertrend = Column(Float, nullable=True)
    vwap = Column(Float, nullable=True)
    ichimoku = Column(Text, nullable=True)  # Store JSON representation or text
    obv = Column(Float, nullable=True)
    cmf = Column(Float, nullable=True)
    mfi = Column(Float, nullable=True)
    roc = Column(Float, nullable=True)
    cci = Column(Float, nullable=True)
    williams_r = Column(Float, nullable=True)
    
    __table_args__ = (
        UniqueConstraint("snapshot_id", "symbol", name="uq_indicator_snapshot_symbol"),
    )


class FeatureSnapshot(Base):
    __tablename__ = "feature_snapshot"
    id = Column(Integer, primary_key=True, autoincrement=True)
    snapshot_id = Column(String, nullable=False)
    symbol = Column(String, nullable=False)
    normalized_values = Column(Text, nullable=True)  # Store JSON string
    z_scores = Column(Text, nullable=True)          # Store JSON string
    rolling_statistics = Column(Text, nullable=True) # Store JSON string
    lag_features = Column(Text, nullable=True)       # Store JSON string
    
    __table_args__ = (
        UniqueConstraint("snapshot_id", "symbol", name="uq_feature_snapshot_symbol"),
    )


class ScoreSnapshot(Base):
    __tablename__ = "score_snapshot"
    id = Column(Integer, primary_key=True, autoincrement=True)
    snapshot_id = Column(String, nullable=False)
    symbol = Column(String, nullable=False)
    strategy_id = Column(String, nullable=False, default="pms_default", server_default="pms_default")
    technical_score = Column(Float, nullable=True)
    ensemble_score = Column(Float, nullable=True)
    gru_score = Column(Float, nullable=True)
    trend_score = Column(Float, nullable=True)
    momentum_score = Column(Float, nullable=True)
    risk_score = Column(Float, nullable=True)
    reliability_score = Column(Float, nullable=True)
    confidence_score = Column(Float, nullable=True)
    composite_score = Column(Float, nullable=True)
    recommendation = Column(String, nullable=True)
    expected_return = Column(Float, nullable=True)
    custom_metrics = Column(Text, nullable=True)  # Store JSON string
    
    __table_args__ = (
        UniqueConstraint("snapshot_id", "symbol", "strategy_id", name="uq_score_snapshot_symbol"),
    )


class ExplainabilitySnapshot(Base):
    __tablename__ = "explainability_snapshot"
    id = Column(Integer, primary_key=True, autoincrement=True)
    snapshot_id = Column(String, nullable=False)
    symbol = Column(String, nullable=False)
    strategy_id = Column(String, nullable=False, default="pms_default", server_default="pms_default")
    score_type = Column(String, nullable=False)
    purpose = Column(Text, nullable=True)
    formula = Column(Text, nullable=True)
    indicator_contributions = Column(Text, nullable=True)  # Store JSON string
    feature_contributions = Column(Text, nullable=True)    # Store JSON string
    current_values = Column(Text, nullable=True)           # Store JSON string
    interpretation = Column(Text, nullable=True)           # Store JSON string
    validation_metrics = Column(Text, nullable=True)       # Store JSON string
    research_references = Column(Text, nullable=True)      # Store JSON string
    
    __table_args__ = (
        UniqueConstraint("snapshot_id", "symbol", "score_type", "strategy_id", name="uq_explainability_snapshot_symbol_score"),
    )




class ReportSnapshot(Base):
    __tablename__ = "report_snapshot"
    id = Column(Integer, primary_key=True, autoincrement=True)
    snapshot_id = Column(String, nullable=False)
    html_report_path = Column(String, nullable=True)
    pdf_report_path = Column(String, nullable=True)
    generation_timestamp = Column(String, nullable=True)
    status = Column(String, nullable=True)


class SnapshotComparison(Base):
    __tablename__ = "snapshot_comparisons"
    snapshot_id_1 = Column(String, primary_key=True)
    snapshot_id_2 = Column(String, primary_key=True)
    strategy_id = Column(String, primary_key=True, default="pms_default", server_default="pms_default")
    date1 = Column(String, nullable=False)
    date2 = Column(String, nullable=False)
    generated_at = Column(String, nullable=False)
    comparison_version = Column(String, nullable=False)


# ── Security Master Seed Data ──
# Nifty 50 + 67 additional popular Indian stocks = 117 total
SECURITY_MASTER_SEED = [
    # ── Nifty 50 ──
    ("RELIANCE.NS", "Reliance Industries Ltd", "Energy", "Oil & Gas Refining"),
    ("TCS.NS", "Tata Consultancy Services Ltd", "Technology", "IT Services"),
    ("HDFCBANK.NS", "HDFC Bank Ltd", "Financial Services", "Private Banks"),
    ("INFY.NS", "Infosys Ltd", "Technology", "IT Services"),
    ("ICICIBANK.NS", "ICICI Bank Ltd", "Financial Services", "Private Banks"),
    ("HINDUNILVR.NS", "Hindustan Unilever Ltd", "Consumer Staples", "FMCG"),
    ("ITC.NS", "ITC Ltd", "Consumer Staples", "FMCG"),
    ("SBIN.NS", "State Bank of India", "Financial Services", "Public Banks"),
    ("BHARTIARTL.NS", "Bharti Airtel Ltd", "Communication", "Telecom"),
    ("KOTAKBANK.NS", "Kotak Mahindra Bank Ltd", "Financial Services", "Private Banks"),
    ("LT.NS", "Larsen & Toubro Ltd", "Industrials", "Construction & Engineering"),
    ("AXISBANK.NS", "Axis Bank Ltd", "Financial Services", "Private Banks"),
    ("ASIANPAINT.NS", "Asian Paints Ltd", "Consumer Discretionary", "Paints"),
    ("MARUTI.NS", "Maruti Suzuki India Ltd", "Consumer Discretionary", "Automobiles"),
    ("TITAN.NS", "Titan Company Ltd", "Consumer Discretionary", "Jewellery"),
    ("SUNPHARMA.NS", "Sun Pharmaceutical Industries Ltd", "Healthcare", "Pharmaceuticals"),
    ("BAJFINANCE.NS", "Bajaj Finance Ltd", "Financial Services", "NBFCs"),
    ("WIPRO.NS", "Wipro Ltd", "Technology", "IT Services"),
    ("ULTRACEMCO.NS", "UltraTech Cement Ltd", "Materials", "Cement"),
    ("HCLTECH.NS", "HCL Technologies Ltd", "Technology", "IT Services"),
    ("NESTLEIND.NS", "Nestle India Ltd", "Consumer Staples", "FMCG"),
    ("POWERGRID.NS", "Power Grid Corp of India Ltd", "Utilities", "Power Transmission"),
    ("NTPC.NS", "NTPC Ltd", "Utilities", "Power Generation"),
    ("TECHM.NS", "Tech Mahindra Ltd", "Technology", "IT Services"),
    ("M&M.NS", "Mahindra & Mahindra Ltd", "Consumer Discretionary", "Automobiles"),
    ("ONGC.NS", "Oil & Natural Gas Corp Ltd", "Energy", "Oil & Gas Exploration"),
    ("TATAMOTORS.NS", "Tata Motors Ltd", "Consumer Discretionary", "Automobiles"),
    ("JSWSTEEL.NS", "JSW Steel Ltd", "Materials", "Steel"),
    ("ADANIENT.NS", "Adani Enterprises Ltd", "Industrials", "Conglomerate"),
    ("ADANIPORTS.NS", "Adani Ports & SEZ Ltd", "Industrials", "Port Services"),
    ("BAJAJFINSV.NS", "Bajaj Finserv Ltd", "Financial Services", "Holding Company"),
    ("TATASTEEL.NS", "Tata Steel Ltd", "Materials", "Steel"),
    ("COALINDIA.NS", "Coal India Ltd", "Energy", "Coal Mining"),
    ("HINDALCO.NS", "Hindalco Industries Ltd", "Materials", "Aluminium"),
    ("GRASIM.NS", "Grasim Industries Ltd", "Materials", "Cement & Textiles"),
    ("CIPLA.NS", "Cipla Ltd", "Healthcare", "Pharmaceuticals"),
    ("DIVISLAB.NS", "Divi's Laboratories Ltd", "Healthcare", "Pharmaceuticals"),
    ("DRREDDY.NS", "Dr. Reddy's Laboratories Ltd", "Healthcare", "Pharmaceuticals"),
    ("EICHERMOT.NS", "Eicher Motors Ltd", "Consumer Discretionary", "Automobiles"),
    ("APOLLOHOSP.NS", "Apollo Hospitals Enterprise Ltd", "Healthcare", "Hospitals"),
    ("SBILIFE.NS", "SBI Life Insurance Co Ltd", "Financial Services", "Insurance"),
    ("BRITANNIA.NS", "Britannia Industries Ltd", "Consumer Staples", "FMCG"),
    ("INDUSINDBK.NS", "IndusInd Bank Ltd", "Financial Services", "Private Banks"),
    ("HEROMOTOCO.NS", "Hero MotoCorp Ltd", "Consumer Discretionary", "Automobiles"),
    ("BPCL.NS", "Bharat Petroleum Corp Ltd", "Energy", "Oil & Gas Refining"),
    ("TATACONSUM.NS", "Tata Consumer Products Ltd", "Consumer Staples", "FMCG"),
    ("BAJAJ-AUTO.NS", "Bajaj Auto Ltd", "Consumer Discretionary", "Automobiles"),
    ("SHRIRAMFIN.NS", "Shriram Finance Ltd", "Financial Services", "NBFCs"),
    ("HDFCLIFE.NS", "HDFC Life Insurance Co Ltd", "Financial Services", "Insurance"),
    ("LTIM.NS", "LTIMindtree Ltd", "Technology", "IT Services"),

    # ── Additional Popular Indian Stocks ──
    ("ZOMATO.NS", "Zomato Ltd", "Consumer Discretionary", "Internet & E-Commerce"),
    ("ONE97COMM.NS", "Paytm (One97 Communications Ltd)", "Technology", "Fintech"),
    ("FSN.NS", "Nykaa (FSN E-Commerce Ventures Ltd)", "Consumer Discretionary", "E-Commerce"),
    ("DMART.NS", "Avenue Supermarts Ltd (DMart)", "Consumer Staples", "Retail"),
    ("HAL.NS", "Hindustan Aeronautics Ltd", "Industrials", "Aerospace & Defence"),
    ("BEL.NS", "Bharat Electronics Ltd", "Industrials", "Defence Electronics"),
    ("IRCTC.NS", "Indian Railway Catering & Tourism Corp", "Industrials", "Travel & Tourism"),
    ("JIOFIN.NS", "Jio Financial Services Ltd", "Financial Services", "NBFCs"),
    ("SUZLON.NS", "Suzlon Energy Ltd", "Utilities", "Renewable Energy"),
    ("LICI.NS", "Life Insurance Corp of India", "Financial Services", "Insurance"),
    ("MRF.NS", "MRF Ltd", "Consumer Discretionary", "Tyres"),
    ("PIDILITIND.NS", "Pidilite Industries Ltd", "Materials", "Adhesives & Chemicals"),
    ("SIEMENS.NS", "Siemens Ltd", "Industrials", "Electrical Equipment"),
    ("ABB.NS", "ABB India Ltd", "Industrials", "Electrical Equipment"),
    ("HAVELLS.NS", "Havells India Ltd", "Consumer Discretionary", "Electrical Equipment"),
    ("VOLTAS.NS", "Voltas Ltd", "Consumer Discretionary", "Consumer Electronics"),
    ("TRENT.NS", "Trent Ltd", "Consumer Discretionary", "Retail"),
    ("PAGEIND.NS", "Page Industries Ltd", "Consumer Discretionary", "Textiles"),
    ("GODREJCP.NS", "Godrej Consumer Products Ltd", "Consumer Staples", "FMCG"),
    ("MARICO.NS", "Marico Ltd", "Consumer Staples", "FMCG"),
    ("COLPAL.NS", "Colgate-Palmolive (India) Ltd", "Consumer Staples", "FMCG"),
    ("DABUR.NS", "Dabur India Ltd", "Consumer Staples", "FMCG"),
    ("BIOCON.NS", "Biocon Ltd", "Healthcare", "Biotechnology"),
    ("LUPIN.NS", "Lupin Ltd", "Healthcare", "Pharmaceuticals"),
    ("TORNTPHARM.NS", "Torrent Pharmaceuticals Ltd", "Healthcare", "Pharmaceuticals"),
    ("AUROPHARMA.NS", "Aurobindo Pharma Ltd", "Healthcare", "Pharmaceuticals"),
    ("PERSISTENT.NS", "Persistent Systems Ltd", "Technology", "IT Services"),
    ("COFORGE.NS", "Coforge Ltd", "Technology", "IT Services"),
    ("MPHASIS.NS", "Mphasis Ltd", "Technology", "IT Services"),
    ("LTTS.NS", "L&T Technology Services Ltd", "Technology", "IT Services"),
    ("INDIGO.NS", "InterGlobe Aviation Ltd (IndiGo)", "Industrials", "Airlines"),
    ("TATAELXSI.NS", "Tata Elxsi Ltd", "Technology", "IT Services"),
    ("POLYCAB.NS", "Polycab India Ltd", "Industrials", "Cables & Wires"),
    ("CUMMINSIND.NS", "Cummins India Ltd", "Industrials", "Industrial Engines"),
    ("BALKRISIND.NS", "Balkrishna Industries Ltd", "Consumer Discretionary", "Tyres"),
    ("PIIND.NS", "PI Industries Ltd", "Materials", "Agrochemicals"),
    ("SOLARINDS.NS", "Solar Industries India Ltd", "Industrials", "Explosives"),
    ("TATAPOWER.NS", "Tata Power Co Ltd", "Utilities", "Power Generation"),
    ("ADANIPOWER.NS", "Adani Power Ltd", "Utilities", "Power Generation"),
    ("ADANIGREEN.NS", "Adani Green Energy Ltd", "Utilities", "Renewable Energy"),
    ("ADANIENSOL.NS", "Adani Energy Solutions Ltd", "Utilities", "Power Transmission"),
    ("VEDL.NS", "Vedanta Ltd", "Materials", "Mining & Metals"),
    ("JINDALSTEL.NS", "Jindal Steel & Power Ltd", "Materials", "Steel"),
    ("SAIL.NS", "Steel Authority of India Ltd", "Materials", "Steel"),
    ("NMDC.NS", "NMDC Ltd", "Materials", "Mining"),
    ("IRFC.NS", "Indian Railway Finance Corp Ltd", "Financial Services", "NBFCs"),
    ("PNB.NS", "Punjab National Bank", "Financial Services", "Public Banks"),
    ("BANKBARODA.NS", "Bank of Baroda", "Financial Services", "Public Banks"),
    ("CANBK.NS", "Canara Bank", "Financial Services", "Public Banks"),
    ("IDFCFIRSTB.NS", "IDFC First Bank Ltd", "Financial Services", "Private Banks"),
    ("FEDERALBNK.NS", "Federal Bank Ltd", "Financial Services", "Private Banks"),
    ("BANDHANBNK.NS", "Bandhan Bank Ltd", "Financial Services", "Private Banks"),
    ("YESBANK.NS", "Yes Bank Ltd", "Financial Services", "Private Banks"),
    ("MANAPPURAM.NS", "Manappuram Finance Ltd", "Financial Services", "NBFCs"),
    ("MUTHOOTFIN.NS", "Muthoot Finance Ltd", "Financial Services", "NBFCs"),
    ("SRF.NS", "SRF Ltd", "Materials", "Chemicals"),
    ("UPL.NS", "UPL Ltd", "Materials", "Agrochemicals"),
    ("DEEPAKNTR.NS", "Deepak Nitrite Ltd", "Materials", "Chemicals"),
    ("ATUL.NS", "Atul Ltd", "Materials", "Chemicals"),
    ("ASTRAL.NS", "Astral Ltd", "Industrials", "Pipes & Fittings"),
    ("CROMPTON.NS", "Crompton Greaves Consumer Electricals", "Consumer Discretionary", "Electrical Equipment"),
    ("WHIRLPOOL.NS", "Whirlpool of India Ltd", "Consumer Discretionary", "Consumer Electronics"),
    ("BATAINDIA.NS", "Bata India Ltd", "Consumer Discretionary", "Footwear"),
    ("VBL.NS", "Varun Beverages Ltd", "Consumer Staples", "Beverages"),
    ("CONCOR.NS", "Container Corp of India Ltd", "Industrials", "Logistics"),
    ("DLF.NS", "DLF Ltd", "Real Estate", "Real Estate Development"),
    ("GODREJPROP.NS", "Godrej Properties Ltd", "Real Estate", "Real Estate Development"),
    ("OBEROIRLTY.NS", "Oberoi Realty Ltd", "Real Estate", "Real Estate Development"),
    ("PRESTIGE.NS", "Prestige Estates Projects Ltd", "Real Estate", "Real Estate Development"),
]


# ── Quant Strategy Studio Tables ───────────────────────────────────────────

class StrategyMaster(Base):
    __tablename__ = "strategy_master"
    strategy_id = Column(String, primary_key=True)  # UUID string
    owner_id = Column(String, nullable=True)
    strategy_name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    strategy_type = Column(String, default="Stock")  # Stock, Portfolio, ETF, Sector, Options, Screening, Allocation
    strategy_prompt = Column(Text, nullable=True)  # search/AI prompt
    strategy_definition = Column(Text, nullable=True)  # JSON string
    visibility = Column(String, default="Private")  # Private, Public, Shared
    version = Column(String, default="1.0.0")
    status = Column(String, default="Draft")  # Draft, Published, Archived
    created_at = Column(String, nullable=True)
    updated_at = Column(String, nullable=True)
    
    versions = relationship("StrategyVersion", back_populates="strategy", cascade="all, delete-orphan")


class StrategyVersion(Base):
    __tablename__ = "strategy_versions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    strategy_id = Column(String, ForeignKey("strategy_master.strategy_id", ondelete="CASCADE"), nullable=False)
    version = Column(String, nullable=False)
    timestamp = Column(String, nullable=False)
    change_summary = Column(Text, nullable=True)
    created_by = Column(String, nullable=True)
    
    strategy = relationship("StrategyMaster", back_populates="versions")


