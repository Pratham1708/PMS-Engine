import logging
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple

from app.services.realtime_feed import fetch_quote_single as raw_fetch_quote, fetch_quotes_batch as raw_fetch_batch
from app.services.historical_data_service import historical_data_service
from app.services.market_data_validator import MarketDataValidator

logger = logging.getLogger(__name__)

def _normalize_market_symbol(symbol: str) -> str:
    """Ensure symbol has exchange suffix (.NS) for Yahoo Finance / market feed calls if missing."""
    s = symbol.upper().strip()
    if s.endswith(".NS") or s.endswith(".BSE"):
        return s
    return f"{s}.NS"


class MarketDataService:
    """
    Unified MarketDataService serves as the single gateway for all market data requests 
    in PMS Engine, enforcing strict data validation checks before returning records.
    """

    @staticmethod
    def get_live_quote(symbol: str) -> Optional[Dict[str, Any]]:
        """
        Fetch and validate live quote for a single symbol.
        Supports inputs both with and without .NS suffix.
        """
        target_symbol = _normalize_market_symbol(symbol)
        logger.info(f"[MarketDataService] Quote Request: {symbol} -> {target_symbol}")
        
        quote = raw_fetch_quote(target_symbol)
        if not quote and target_symbol != symbol.upper().strip():
            quote = raw_fetch_quote(symbol.upper().strip())

        if not quote:
            logger.warning(f"[MarketDataService] Quote download failed or returned None for {symbol}")
            return None

        is_valid, errors = MarketDataValidator.validate_quote(quote, quote.get("Symbol", symbol))
        if not is_valid:
            logger.error(f"[MarketDataService] Quote validation failed for {symbol}: {errors}")
            return None

        logger.info(f"[MarketDataService] Quote Success: {symbol} @ ₹{quote['CurrentPrice']}")
        return quote

    @staticmethod
    def get_live_quotes_batch(symbols: List[str]) -> pd.DataFrame:
        """
        Fetch and validate quotes for a list of symbols.
        Returns a DataFrame of validated quotes.
        """
        normalized_symbols = [_normalize_market_symbol(s) for s in symbols]
        logger.info(f"[MarketDataService] Batch Quotes Request: {len(symbols)} symbols")
        
        raw_df = raw_fetch_batch(normalized_symbols)
        if raw_df.empty:
            return pd.DataFrame()

        validated_quotes = []
        for _, row in raw_df.iterrows():
            quote_dict = row.to_dict()
            is_valid, _ = MarketDataValidator.validate_quote(quote_dict, quote_dict.get("Symbol", ""))
            if is_valid:
                validated_quotes.append(quote_dict)
            else:
                logger.warning(f"[MarketDataService] Excluding stale/invalid batch quote for {quote_dict.get('Symbol')}")

        if not validated_quotes:
            return pd.DataFrame()

        return pd.DataFrame(validated_quotes)

    @staticmethod
    def get_historical_data(symbol: str, period: str) -> Optional[pd.DataFrame]:
        """
        Fetch and validate historical price series DataFrame.
        Supports inputs both with and without .NS suffix.
        """
        target_symbol = _normalize_market_symbol(symbol)
        logger.info(f"[MarketDataService] History Request: {symbol} ({period}) -> {target_symbol}")
        
        df = historical_data_service.get_stock_history(target_symbol, period)
        if (df is None or df.empty) and target_symbol != symbol.upper().strip():
            df = historical_data_service.get_stock_history(symbol.upper().strip(), period)

        if df is None or df.empty:
            logger.warning(f"[MarketDataService] History download returned empty or None for {symbol} ({period})")
            return None

        is_valid, errors = MarketDataValidator.validate_historical_df(df, target_symbol, period)
        if not is_valid:
            logger.error(f"[MarketDataService] History validation failed for {symbol}: {errors}")
            return None

        logger.info(f"[MarketDataService] History Success: {symbol} ({period}) -> {len(df)} validated bars")
        return df

# Singleton instance
market_data_service = MarketDataService()
