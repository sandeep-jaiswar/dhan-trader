"""
Stock data fetching service.
Fetches OHLCV and fundamental data from TradingView, NSE, or yfinance sources.
"""

import logging
from typing import Optional, Dict, List

logger = logging.getLogger(__name__)


class StockDataFetcher:
    @staticmethod
    def fetch(symbol: str, interval: str = "1d", n: int = 100) -> Optional[dict]:
        """
        Fetch OHLCV data for given symbol and interval.
        
        Args:
            symbol: Stock symbol (e.g., "NSE:INFY", "RELIANCE")
            interval: Time interval (e.g., "1d", "1h", "15m")
            n: Number of candles to fetch
            
        Returns:
            Dictionary with OHLCV data or None if fetch fails
            Format: {
                'open': [float, ...],
                'high': [float, ...],
                'low': [float, ...],
                'close': [float, ...],
                'volume': [float, ...]
            }
        """
        try:
            # Try yfinance first
            return StockDataFetcher._fetch_yfinance(symbol, interval, n)
        except Exception as e:
            logger.error(f"Failed to fetch data for {symbol}: {e}")
            return None

    @staticmethod
    def _fetch_yfinance(symbol: str, interval: str = "1d", n: int = 100) -> Optional[dict]:
        """
        Fetch data using yfinance library.
        """
        try:
            import yfinance as yf
        except ImportError:
            logger.warning("yfinance not installed. Install with: pip install yfinance")
            return None
        
        try:
            # Convert NSE:SYMBOL format to SYMBOL.NS for yfinance
            ticker_symbol = symbol
            if ":" in symbol:
                exchange, ticker = symbol.split(":", 1)
                if exchange == "NSE":
                    ticker_symbol = f"{ticker}.NS"
                elif exchange == "BSE":
                    ticker_symbol = f"{ticker}.BO"
                else:
                    ticker_symbol = ticker
            
            # Map interval to appropriate period
            # yfinance periods: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
            interval_to_period = {
                "1m": "1d",
                "5m": "5d",
                "15m": "1mo",
                "30m": "1mo",
                "1h": "3mo",
                "1d": f"{n}d" if n < 730 else "max",
                "1w": f"{int(n/5)}d" if n < 3650 else "max",
                "1M": "max"
            }
            
            period = interval_to_period.get(interval, f"{n}d")
            
            # Fetch data
            ticker = yf.Ticker(ticker_symbol)
            df = ticker.history(period=period, interval=interval)
            
            if df.empty:
                logger.warning(f"No data returned for {symbol}")
                return None
            
            # Limit to requested number of candles
            if len(df) > n:
                df = df.tail(n)
            
            # Convert to dict format
            return {
                'open': df['Open'].tolist(),
                'high': df['High'].tolist(),
                'low': df['Low'].tolist(),
                'close': df['Close'].tolist(),
                'volume': df['Volume'].tolist()
            }
        except Exception as e:
            logger.error(f"yfinance fetch failed for {symbol}: {e}")
            return None

    @staticmethod
    def _fetch_tvdatafeed(symbol: str, interval: str = "1d", n: int = 100) -> Optional[dict]:
        """
        Fetch data using tvdatafeed library (TradingView).
        Placeholder for future implementation.
        """
        try:
            from tvdatafeed import TvDatafeed, Interval
        except ImportError:
            logger.warning("tvdatafeed not installed")
            return None
        
        try:
            # Parse symbol
            exchange = "NSE"
            ticker = symbol
            if ":" in symbol:
                exchange, ticker = symbol.split(":", 1)
            
            # Map interval string to TvDatafeed interval
            interval_map = {
                "1m": Interval.in_1_minute,
                "5m": Interval.in_5_minute,
                "15m": Interval.in_15_minute,
                "1h": Interval.in_1_hour,
                "1d": Interval.in_daily,
                "1w": Interval.in_weekly,
            }
            tv_interval = interval_map.get(interval, Interval.in_daily)
            
            # Fetch data
            tv = TvDatafeed()
            df = tv.get_hist(symbol=ticker, exchange=exchange, interval=tv_interval, n_bars=n)
            
            if df is None or df.empty:
                return None
            
            return {
                'open': df['open'].tolist(),
                'high': df['high'].tolist(),
                'low': df['low'].tolist(),
                'close': df['close'].tolist(),
                'volume': df['volume'].tolist()
            }
        except Exception as e:
            logger.error(f"tvdatafeed fetch failed for {symbol}: {e}")
            return None
