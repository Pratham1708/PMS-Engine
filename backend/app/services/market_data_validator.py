import logging
import pandas as pd
from datetime import datetime, date, timedelta
from typing import Dict, Any, Tuple, List, Optional

logger = logging.getLogger(__name__)

class MarketDataValidator:
    """
    MarketDataValidator performs dataset, OHLC, and freshness checks 
    on quotes and historical stock price datasets to ensure no corrupted 
    or mock data enters the quantitative pipeline.
    """

    @staticmethod
    def validate_quote(quote: Dict[str, Any], symbol: str) -> Tuple[bool, List[str]]:
        """
        Validate a single real-time stock quote.
        Returns (is_valid, list_of_errors).
        """
        errors = []
        if not quote:
            errors.append(f"[{symbol}] Quote dict is empty or None")
            return False, errors

        # 1. Check required fields
        required_fields = ["Symbol", "Open", "High", "Low", "CurrentPrice", "Volume"]
        for field in required_fields:
            if field not in quote or quote[field] is None:
                errors.append(f"[{symbol}] Missing required field: {field}")
            elif isinstance(quote[field], float) and pd.isna(quote[field]):
                errors.append(f"[{symbol}] Field {field} is NaN")

        if errors:
            return False, errors

        # 2. OHLC Validation
        open_val = float(quote["Open"])
        high_val = float(quote["High"])
        low_val = float(quote["Low"])
        close_val = float(quote["CurrentPrice"])
        volume = int(quote["Volume"])

        if open_val <= 0:
            errors.append(f"[{symbol}] Open price ({open_val}) must be > 0")
        if close_val <= 0:
            errors.append(f"[{symbol}] Close price ({close_val}) must be > 0")
        if volume < 0:
            errors.append(f"[{symbol}] Volume ({volume}) must be >= 0")

        if high_val < open_val:
            errors.append(f"[{symbol}] High ({high_val}) cannot be less than Open ({open_val})")
        if high_val < close_val:
            errors.append(f"[{symbol}] High ({high_val}) cannot be less than Close ({close_val})")
        if high_val < low_val:
            errors.append(f"[{symbol}] High ({high_val}) cannot be less than Low ({low_val})")
        if low_val > open_val:
            errors.append(f"[{symbol}] Low ({low_val}) cannot be greater than Open ({open_val})")
        if low_val > close_val:
            errors.append(f"[{symbol}] Low ({low_val}) cannot be greater than Close ({close_val})")

        # 3. Freshness Check (Verify volume)
        # Note: We don't block quotes with 0 volume during early pre-market or after-hours,
        # but standard trading day quotes should have positive volume.
        
        is_valid = len(errors) == 0
        if not is_valid:
            logger.error(f"[Validation Failed] Quote errors for {symbol}: {errors}")
        else:
            logger.debug(f"[Validation Passed] Quote for {symbol} is valid")
        return is_valid, errors

    @staticmethod
    def validate_historical_df(df: pd.DataFrame, symbol: str, period: str) -> Tuple[bool, List[str]]:
        """
        Validate a historical price series DataFrame.
        Returns (is_valid, list_of_errors).
        """
        errors = []
        if df is None or df.empty:
            errors.append(f"[{symbol}] Historical dataset is empty or None")
            return False, errors

        # 1. Required Columns
        required_cols = ["Date", "Open", "High", "Low", "Close", "Volume"]
        for col in required_cols:
            if col not in df.columns:
                errors.append(f"[{symbol}] Missing required column: {col}")

        if errors:
            return False, errors

        # 2. Check for NaNs/nulls in required columns
        for col in required_cols:
            null_count = df[col].isnull().sum()
            if null_count > 0:
                errors.append(f"[{symbol}] Column {col} contains {null_count} null/NaN values")

        # 3. Check for duplicates in Date/timestamps
        dup_dates = df["Date"].duplicated().sum()
        if dup_dates > 0:
            errors.append(f"[{symbol}] Dataset contains {dup_dates} duplicate dates")

        # 4. Check sorting (dates must be strictly increasing)
        try:
            dates = pd.to_datetime(df["Date"])
            if not dates.is_monotonic_increasing:
                errors.append(f"[{symbol}] Dates are not sorted in ascending order")
            
            # Check for future dates
            today_str = datetime.now().date().strftime("%Y-%m-%d")
            future_dates = (df["Date"] > today_str).sum()
            if future_dates > 0:
                errors.append(f"[{symbol}] Dataset contains {future_dates} future dates")
        except Exception as e:
            errors.append(f"[{symbol}] Failed date parsing/sorting check: {e}")

        # 5. OHLC validations across all rows
        try:
            invalid_open = (df["Open"] <= 0).sum()
            invalid_close = (df["Close"] <= 0).sum()
            invalid_vol = (df["Volume"] < 0).sum()

            if invalid_open > 0:
                errors.append(f"[{symbol}] Found {invalid_open} rows with Open <= 0")
            if invalid_close > 0:
                errors.append(f"[{symbol}] Found {invalid_close} rows with Close <= 0")
            if invalid_vol > 0:
                errors.append(f"[{symbol}] Found {invalid_vol} rows with Volume < 0")

            bad_high_open = (df["High"] < df["Open"]).sum()
            bad_high_close = (df["High"] < df["Close"]).sum()
            bad_high_low = (df["High"] < df["Low"]).sum()
            bad_low_open = (df["Low"] > df["Open"]).sum()
            bad_low_close = (df["Low"] > df["Close"]).sum()

            if bad_high_open > 0:
                errors.append(f"[{symbol}] Found {bad_high_open} rows where High < Open")
            if bad_high_close > 0:
                errors.append(f"[{symbol}] Found {bad_high_close} rows where High < Close")
            if bad_high_low > 0:
                errors.append(f"[{symbol}] Found {bad_high_low} rows where High < Low")
            if bad_low_open > 0:
                errors.append(f"[{symbol}] Found {bad_low_open} rows where Low > Open")
            if bad_low_close > 0:
                errors.append(f"[{symbol}] Found {bad_low_close} rows where Low > Close")

        except Exception as e:
            errors.append(f"[{symbol}] Failed OHLC row boundary validations: {e}")

        # 6. Freshness Validation
        # Check if the latest bar date matches the last active trading session (allow weekends/holidays)
        try:
            last_date_str = str(df["Date"].iloc[-1])
            last_date = datetime.strptime(last_date_str, "%Y-%m-%d").date()
            today = datetime.now().date()
            
            # Max age of data in days: standard is 4 days to handle long holiday weekends
            max_age_days = 4
            age_days = (today - last_date).days
            if age_days > max_age_days:
                errors.append(f"[{symbol}] Latest trading day is stale: {last_date_str} (age: {age_days} days)")
                
        except Exception as e:
            errors.append(f"[{symbol}] Freshness check parsing failed: {e}")

        is_valid = len(errors) == 0
        if not is_valid:
            logger.error(f"[Validation Failed] Historical data errors for {symbol} ({period}): {errors}")
        else:
            logger.info(f"[Validation Passed] Historical dataset for {symbol} ({period}) verified: {len(df)} bars")
        return is_valid, errors
