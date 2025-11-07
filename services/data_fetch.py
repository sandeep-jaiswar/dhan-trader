"""
Stock data fetching service.
Improvements: small refactor to add retries, basic caching integration, symbol parsing and
safer DataFrame access. Keeps a minimal public API: StockDataFetcher.fetch(...)
"""

import logging
import time
from typing import Optional, Dict

from utils.validators import validate_symbol
from utils.cache import cache

logger = logging.getLogger(__name__)


class StockDataFetcher:
    """Fetch OHLCV data from available providers (yfinance primary, tvdatafeed optional)."""

    # Map simple interval -> yfinance period fallback
    INTERVAL_TO_PERIOD = {
        "1m": "1d",
        "5m": "5d",
        "15m": "1mo",
        "30m": "1mo",
        "1h": "3mo",
        "1d": "1y",
        "1w": "5y",
        "1M": "max",
    }

    @staticmethod
    def _parse_symbol_for_yf(symbol: str) -> str:
        """Convert symbols like 'NSE:INFY' to yfinance tickers like 'INFY.NS'."""
        if ":" in symbol:
            exchange, ticker = symbol.split(":", 1)
            exchange = exchange.upper()
            ticker = ticker.strip()
            if exchange == "NSE":
                return f"{ticker}.NS"
            if exchange == "BSE":
                return f"{ticker}.BO"
            return ticker
        return symbol

    @staticmethod
    def fetch(symbol: str, interval: str = "1d", n: int = 100) -> Optional[Dict[str, list]]:
        """
        Public fetch method.

        - Validates symbol format
        - Uses cache (best-effort)
        - Attempts yfinance fetch with retries
        - Falls back to tvdatafeed if configured (not installed by default)

        Returns OHLCV dict or None.
        """
        try:
            validate_symbol(symbol)
        except Exception as e:
            logger.debug("Symbol validation failed", exc_info=True)
            raise

        cache_key = f"ohlcv:{symbol}:{interval}:{n}"
        try:
            cached = cache.get(cache_key)
            if cached:
                logger.debug("Returning cached OHLCV for %s", symbol)
                return cached
        except Exception:
            # Cache issues should not block fetch
            logger.debug("Cache get failed (continuing to fetch)", exc_info=True)

        # Try yfinance first
        data = StockDataFetcher._fetch_yfinance(symbol, interval, n)
        if data:
            try:
                cache.set(cache_key, data, ttl_hours=getattr(cache, "TTL_STOCK_DATA", 1))
            except Exception:
                logger.debug("Cache set failed", exc_info=True)
            return data

        # Try TradingView via tvdatafeed as a fallback (optional)
        data = StockDataFetcher._fetch_tvdatafeed(symbol, interval, n)
        if data:
            try:
                cache.set(cache_key, data, ttl_hours=getattr(cache, "TTL_STOCK_DATA", 1))
            except Exception:
                logger.debug("Cache set failed", exc_info=True)
            return data

        return None

    @staticmethod
    def _fetch_yfinance(symbol: str, interval: str = "1d", n: int = 100) -> Optional[Dict[str, list]]:
        """
        Fetch data using yfinance with simple retries.
        """
        try:
            import yfinance as yf
        except ImportError:
            logger.warning("yfinance not installed. Install with: pip install yfinance")
            return None

        ticker_symbol = StockDataFetcher._parse_symbol_for_yf(symbol)
        period = StockDataFetcher.INTERVAL_TO_PERIOD.get(interval, f"{n}d")

        attempts = 3
        backoff = 1
        last_exc = None
        for attempt in range(1, attempts + 1):
            try:
                ticker = yf.Ticker(ticker_symbol)
                df = ticker.history(period=period, interval=interval)

                if df is None or df.empty:
                    logger.debug("yfinance returned empty DataFrame for %s (attempt %d)", symbol, attempt)
                    return None

                # Ensure we have required columns
                required = ["Open", "High", "Low", "Close", "Volume"]
                if not all(col in df.columns for col in required):
                    logger.error("Missing columns from yfinance data for %s: %s", symbol, df.columns.tolist())
                    return None

                if len(df) > n:
                    df = df.tail(n)

                return {
                    "open": df["Open"].tolist(),
                    "high": df["High"].tolist(),
                    "low": df["Low"].tolist(),
                    "close": df["Close"].tolist(),
                    "volume": df["Volume"].tolist(),
                }

            except Exception as e:
                last_exc = e
                logger.warning("yfinance attempt %d failed for %s: %s", attempt, symbol, e)
                time.sleep(backoff)
                backoff *= 2

        logger.error("yfinance failed after %d attempts for %s: %s", attempts, symbol, last_exc, exc_info=True)
        return None

    @staticmethod
    def _fetch_tvdatafeed(symbol: str, interval: str = "1d", n: int = 100) -> Optional[Dict[str, list]]:
        """
        Optional TradingView fetch using tvdatafeed. Returns None if library not installed.
        """
        try:
            from tvdatafeed import TvDatafeed, Interval
        except ImportError:
            logger.debug("tvdatafeed not installed; skipping TradingView fetch")
            return None

        try:
            exchange = "NSE"
            ticker = symbol
            if ":" in symbol:
                exchange, ticker = symbol.split(":", 1)

            interval_map = {
                "1m": Interval.in_1_minute,
                "5m": Interval.in_5_minute,
                "15m": Interval.in_15_minute,
                "1h": Interval.in_1_hour,
                "1d": Interval.in_daily,
                "1w": Interval.in_weekly,
            }

            tv_interval = interval_map.get(interval)
            if tv_interval is None:
                logger.error("Unsupported interval for tvdatafeed: %s", interval)
                return None

            tv = TvDatafeed()
            df = tv.get_hist(symbol=ticker, exchange=exchange, interval=tv_interval, n_bars=n)

            if df is None or df.empty:
                return None

            required = ["open", "high", "low", "close", "volume"]
            if not all(col in df.columns for col in required):
                logger.error("Missing columns from tvdatafeed for %s: %s", symbol, df.columns.tolist())
                return None

            return {
                "open": df["open"].tolist(),
                "high": df["high"].tolist(),
                "low": df["low"].tolist(),
                "close": df["close"].tolist(),
                "volume": df["volume"].tolist(),
            }

        except Exception as e:
            logger.error("tvdatafeed fetch failed for %s: %s", symbol, e, exc_info=True)
            return None

