"""
PMS Engine Data Loader.
Loads final_institutional_scanner.csv into memory and provides cached access.
Supports hot-reload via refresh() without server restart.
"""

import pandas as pd
import logging
from typing import Optional

from app.config import settings

logger = logging.getLogger(__name__)

# Columns expected in the CSV
EXPECTED_COLUMNS = [
    "Symbol",
    "FrontendSignal",
    "FinalRating",
    "Confidence",
    "CompositeScoreV2",
    "TechnicalScore",
    "MLScore",
    "GRUScore",
    "ReliabilityScore",
]

# Numeric columns to round
NUMERIC_COLUMNS = [
    "Confidence",
    "CompositeScoreV2",
    "TechnicalScore",
    "MLScore",
    "GRUScore",
    "ReliabilityScore",
]


class DataLoader:
    """
    In-memory data loader for the PMS Engine scanner CSV.
    Architected as a class so it can be replaced with a DatabaseLoader
    when PostgreSQL is introduced in a future phase.
    """

    def __init__(self) -> None:
        self._df: Optional[pd.DataFrame] = None
        self.last_market_update: Optional[str] = None
        self.last_scanner_run: Optional[str] = None
        self._load()

    def _load(self) -> None:
        """Load CSV from disk into memory, merge GRU data, and calculate ranks/percentiles."""
        try:
            df = pd.read_csv(settings.csv_path)

            # Validate columns
            missing = set(EXPECTED_COLUMNS) - set(df.columns)
            if missing:
                logger.warning(f"Missing expected columns: {missing}")

            # Round numeric columns
            for col in NUMERIC_COLUMNS:
                if col in df.columns:
                    df[col] = df[col].round(2)

            # Add Sector placeholder for future expansion
            df["Sector"] = "\u2014"

            # Drop FrontendSignal — we only use FinalRating
            if "FrontendSignal" in df.columns:
                df = df.drop(columns=["FrontendSignal"])

            # Safe validation and merge of GRU / ReturnScore columns from gru_scanner_results.csv
            import os
            base_dir = os.path.dirname(os.path.abspath(settings.csv_path))
            gru_path = os.path.join(base_dir, "data", "live", "gru_scanner_results.csv")
            gru_paths_to_try = [
                gru_path,
                os.path.join(os.path.dirname(os.path.abspath(__file__)), "gru_scanner_results.csv"),
                os.path.join(base_dir, "gru_scanner_results.csv"),
                os.path.join(base_dir, "live", "gru_scanner_results.csv"),
                os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "data", "live", "gru_scanner_results.csv"),
                "backend/app/data/gru_scanner_results.csv"
            ]
            
            gru_df = None
            found_gru_path = None
            for p in gru_paths_to_try:
                if os.path.exists(p):
                    try:
                        gru_df = pd.read_csv(p)
                        found_gru_path = p
                        break
                    except Exception as ex:
                        logger.warning(f"Failed to read GRU file at {p}: {ex}")

            if gru_df is not None:
                gru_cols = ["Symbol"]
                for col in ["GRU_HOLD", "GRU_LONG", "GRU_SHORT", "ReturnScore"]:
                    if col in gru_df.columns:
                        gru_cols.append(col)
                if len(gru_cols) > 1:
                    df = pd.merge(df, gru_df[gru_cols], on="Symbol", how="left")
                    logger.info(f"Successfully merged GRU/Return columns {gru_cols[1:]} from {found_gru_path}")
            else:
                logger.warning("Could not locate or load gru_scanner_results.csv. GRU fields will remain null.")

            # Ensure all XAI and live market columns exist (filled with None if not merged)
            for col in [
                "GRU_HOLD", "GRU_LONG", "GRU_SHORT", "ReturnScore",
                "CurrentPrice", "Open", "High", "Low", "Volume",
                "PreviousClose", "DailyChangePct", "DailyChangeAmount"
            ]:
                if col not in df.columns:
                    df[col] = None

            # Sort by CompositeScoreV2 descending for ranking
            df = df.sort_values(by="CompositeScoreV2", ascending=False).reset_index(drop=True)
            
            # Ranks must be exactly 1 to 50 based on universe size
            df["Rank"] = df.index + 1
            total_stocks = len(df)

            # Dynamic percentile calculation: (1 - (rank - 1) / (total_stocks - 1)) * 100
            if total_stocks > 1:
                df["Percentile"] = (1 - (df["Rank"] - 1) / (total_stocks - 1)) * 100
            else:
                df["Percentile"] = 100.0
            
            df["Percentile"] = df["Percentile"].round(2)

            # Assign UniversePosition based on Percentile
            def assign_position(pct):
                if pct >= 90.0: return "Top Decile"
                if pct >= 75.0: return "Upper Quartile"
                if pct >= 25.0: return "Middle Quartile"
                if pct >= 10.0: return "Lower Quartile"
                return "Bottom Decile"
                
            df["UniversePosition"] = df["Percentile"].apply(assign_position)

            # Add PortfolioEligible derived from FinalRating in ["STRONG BUY", "BUY"]
            df["PortfolioEligible"] = df["FinalRating"].isin(["STRONG BUY", "BUY"])

            # Add ConvictionLevel derived from Confidence
            def assign_conviction(conf):
                if conf >= 80.0: return "High Conviction"
                if conf >= 60.0: return "Medium Conviction"
                return "Low Conviction"
                
            df["ConvictionLevel"] = df["Confidence"].apply(assign_conviction)

            import pytz
            from datetime import datetime
            ist = pytz.timezone("Asia/Kolkata")
            now_str = datetime.now(ist).strftime("%Y-%m-%d %I:%M:%S %p IST")
            if self.last_scanner_run is None:
                self.last_scanner_run = now_str
            if self.last_market_update is None:
                self.last_market_update = "N/A"

            self._df = df
            logger.info(f"Loaded and enriched {len(df)} stocks. Ranks assigned 1-{len(df)}.")

        except FileNotFoundError:
            logger.error(f"CSV not found: {settings.csv_path}")
            self._df = pd.DataFrame()
        except Exception as e:
            logger.error(f"Error loading CSV: {e}")
            self._df = pd.DataFrame()

    def refresh(self) -> int:
        """Reload CSV from disk. Returns number of stocks loaded."""
        self._load()
        return len(self._df)

    def get_df(self) -> pd.DataFrame:
        """Return the cached DataFrame."""
        if self._df is None:
            self._load()
        return self._df.copy()

    @property
    def stocks_loaded(self) -> int:
        """Number of stocks currently in memory."""
        return len(self._df) if self._df is not None else 0


# Singleton instance
data_loader = DataLoader()
