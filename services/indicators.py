"""Technical indicator calculation utilities.
Implements indicators used for scoring and signal generation.

Notes:
- All indicator methods return a list with the same length as the input price
    series. Values that cannot be computed for early indices are set to None.
"""

from typing import List, Optional, Dict, Any


class IndicatorCalculator:
    @staticmethod
    def ema(prices: List[float], period: int) -> List[Optional[float]]:
        """Calculate Exponential Moving Average (EMA).

        Returns a list the same length as `prices`. Early entries which cannot be
        computed are set to None.
        """
        ema_list: List[Optional[float]] = []
        if period <= 0:
            raise ValueError("period must be > 0")

        k = 2 / (period + 1)
        for i, price in enumerate(prices):
            if i < period - 1:
                ema_list.append(None)
            elif i == period - 1:
                ema_list.append(sum(prices[:period]) / period)
            else:
                prev = ema_list[-1]
                # prev should not be None here
                ema = price * k + (prev if prev is not None else price) * (1 - k)
                ema_list.append(ema)
        return ema_list

    @staticmethod
    def rsi(prices: List[float], period: int = 14) -> List[Optional[float]]:
        """Calculate Relative Strength Index (RSI).

        Returns list of same length as `prices`, with initial values set to None.
        """
        if period <= 0:
            raise ValueError("period must be > 0")

        n = len(prices)
        if n < period + 1:
            return [None] * n

        deltas = [prices[i] - prices[i - 1] for i in range(1, n)]
        seed = deltas[:period]
        avg_gain = sum(x for x in seed if x > 0) / period
        avg_loss = -sum(x for x in seed if x < 0) / period

        rsi_values: List[Optional[float]] = [None] * period
        # first RSI value
        if avg_loss == 0:
            rsi_values.append(100.0)
        else:
            rs = avg_gain / avg_loss
            rsi_values.append(100 - 100 / (1 + rs))

        for delta in deltas[period:]:
            gain = max(delta, 0)
            loss = -min(delta, 0)
            avg_gain = (avg_gain * (period - 1) + gain) / period
            avg_loss = (avg_loss * (period - 1) + loss) / period
            if avg_loss == 0:
                rsi_values.append(100.0)
            else:
                rs = avg_gain / avg_loss
                rsi_values.append(100 - 100 / (1 + rs))

        return rsi_values

    @staticmethod
    def mfi(highs: List[float], lows: List[float], closes: List[float], volumes: List[float], period: int = 14) -> List[Optional[float]]:
        """Calculate Money Flow Index (MFI).

        MFI is a volume-weighted momentum indicator. Returns list matching length
        of closes with None for early entries.
        """
        if period <= 0:
            raise ValueError("period must be > 0")

        n = len(closes)
        if n < period + 1:
            return [None] * n

        typical_prices = [(h + l + c) / 3 for h, l, c in zip(highs, lows, closes)]
        money_flows = [tp * v for tp, v in zip(typical_prices, volumes)]

        mfi_values: List[Optional[float]] = [None] * period
        for i in range(period, n):
            positive_flow = sum(money_flows[j] for j in range(i - period, i) if typical_prices[j] > typical_prices[j - 1])
            negative_flow = sum(money_flows[j] for j in range(i - period, i) if typical_prices[j] < typical_prices[j - 1])

            if negative_flow == 0:
                mfi = 100.0
            else:
                money_ratio = positive_flow / negative_flow
                mfi = 100 - (100 / (1 + money_ratio))

            mfi_values.append(mfi)

        return mfi_values

    @staticmethod
    def obv(closes: List[float], volumes: List[float]) -> List[Optional[float]]:
        """Calculate On-Balance Volume (OBV)."""
        if not closes:
            return []

        obv_values: List[Optional[float]] = [0]
        current_obv = 0

        for i in range(1, len(closes)):
            if closes[i] > closes[i - 1]:
                current_obv += volumes[i]
            elif closes[i] < closes[i - 1]:
                current_obv -= volumes[i]
            obv_values.append(current_obv)

        return obv_values

    @staticmethod
    def vwap(highs: List[float], lows: List[float], closes: List[float], volumes: List[float]) -> List[Optional[float]]:
        """Calculate Volume Weighted Average Price (VWAP)."""
        vwap_values: List[Optional[float]] = []
        cumulative_tp_volume = 0.0
        cumulative_volume = 0.0

        for h, l, c, v in zip(highs, lows, closes, volumes):
            typical_price = (h + l + c) / 3
            cumulative_tp_volume += typical_price * v
            cumulative_volume += v

            if cumulative_volume == 0:
                vwap_values.append(None)
            else:
                vwap_values.append(cumulative_tp_volume / cumulative_volume)

        return vwap_values

    @staticmethod
    def ad_line(highs: List[float], lows: List[float], closes: List[float], volumes: List[float]) -> List[Optional[float]]:
        """Calculate Accumulation/Distribution Line (A/D)."""
        ad_values: List[Optional[float]] = []
        cumulative_ad = 0.0

        for h, l, c, v in zip(highs, lows, closes, volumes):
            if h == l:
                clv = 0.0
            else:
                clv = ((c - l) - (h - c)) / (h - l)

            cumulative_ad += clv * v
            ad_values.append(cumulative_ad)

        return ad_values

    @staticmethod
    def sma(prices: List[float], period: int) -> List[Optional[float]]:
        """Calculate Simple Moving Average (SMA)."""
        if period <= 0:
            raise ValueError("period must be > 0")

        sma_list: List[Optional[float]] = []
        for i in range(len(prices)):
            if i < period - 1:
                sma_list.append(None)
            else:
                sma = sum(prices[i - period + 1:i + 1]) / period
                sma_list.append(sma)
        return sma_list

    @staticmethod
    def macd(prices: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, List[Optional[float]]]:
        """Calculate MACD and signal/histogram.

        Returns a dict with keys: 'macd', 'signal', 'histogram' (each a list).
        """
        ema_fast = IndicatorCalculator.ema(prices, fast)
        ema_slow = IndicatorCalculator.ema(prices, slow)

        macd_line: List[Optional[float]] = []
        for f, s in zip(ema_fast, ema_slow):
            if f is None or s is None:
                macd_line.append(None)
            else:
                macd_line.append(f - s)

        # Calculate signal line (EMA of MACD) - only use non-None values
        non_none_indices = [i for i, x in enumerate(macd_line) if x is not None]
        if non_none_indices:
            signal_prices = [macd_line[i] for i in non_none_indices]
            signal_ema = IndicatorCalculator.ema(signal_prices, signal)

            signal_line: List[Optional[float]] = [None] * len(macd_line)
            for i, idx in enumerate(non_none_indices):
                # signal_ema length == len(signal_prices) == len(non_none_indices)
                signal_line[idx] = signal_ema[i]
        else:
            signal_line = [None] * len(macd_line)

        histogram: List[Optional[float]] = []
        for m, s in zip(macd_line, signal_line):
            if m is None or s is None:
                histogram.append(None)
            else:
                histogram.append(m - s)

        return {
            'macd': macd_line,
            'signal': signal_line,
            'histogram': histogram
        }

    @staticmethod
    def atr(highs: List[float], lows: List[float], closes: List[float], period: int = 14) -> List[Optional[float]]:
        """Calculate Average True Range (ATR).

        Returns list matching length of `closes`, with None for early indices.
        """
        if period <= 0:
            raise ValueError("period must be > 0")

        n = len(closes)
        if n < 2:
            return [None] * n

        true_ranges: List[float] = [highs[0] - lows[0]]
        for i in range(1, n):
            tr = max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i - 1]),
                abs(lows[i] - closes[i - 1])
            )
            true_ranges.append(tr)

        # Need at least `period` true ranges to compute initial ATR
        if len(true_ranges) < period:
            return [None] * n

        atr_values: List[Optional[float]] = [None] * (period - 1)
        atr = sum(true_ranges[:period]) / period
        atr_values.append(atr)

        for i in range(period, len(true_ranges)):
            atr = (atr * (period - 1) + true_ranges[i]) / period
            atr_values.append(atr)

        return atr_values

    @staticmethod
    def bollinger_bands(prices: List[float], period: int = 20, std_dev: float = 2.0) -> Dict[str, List[Optional[float]]]:
        """Calculate Bollinger Bands. Returns dict with 'upper','middle','lower'."""
        middle_band = IndicatorCalculator.sma(prices, period)
        upper_band: List[Optional[float]] = []
        lower_band: List[Optional[float]] = []

        for i in range(len(prices)):
            if i < period - 1:
                upper_band.append(None)
                lower_band.append(None)
            else:
                window = prices[i - period + 1:i + 1]
                std = (sum((x - middle_band[i]) ** 2 for x in window) / period) ** 0.5
                mid = middle_band[i] if middle_band[i] is not None else sum(window) / period
                upper_band.append(mid + std_dev * std)
                lower_band.append(mid - std_dev * std)

        return {
            'upper': upper_band,
            'middle': middle_band,
            'lower': lower_band
        }

    @staticmethod
    def detect_bullish_candle(opens: List[float], highs: List[float], lows: List[float], closes: List[float], idx: int) -> bool:
        """Detect bullish candlestick patterns at given index.

        Basic checks: Hammer, Bullish Engulfing.
        """
        if idx < 2 or idx >= len(closes):
            return False

        o, h, l, c = opens[idx], highs[idx], lows[idx], closes[idx]
        body = abs(c - o)
        range_hl = h - l

        o_prev, c_prev = opens[idx - 1], closes[idx - 1]

        # Hammer-like
        if c > o and range_hl > 0:
            lower_wick = o - l
            upper_wick = h - c
            if lower_wick > 2 * body and upper_wick < body * 0.1:
                return True

        # Bullish Engulfing
        if c > o and c_prev < o_prev:
            if c > o_prev and o < c_prev:
                return True

        return False

    @staticmethod
    def is_uptrend(prices: List[float], period: int = 50, lookback: int = 10) -> bool:
        """Check if prices are in uptrend using moving average comparison."""
        if len(prices) < period + lookback:
            return False

        recent_ma = sum(prices[-period:]) / period
        older_ma = sum(prices[-period - lookback:-lookback]) / period
        return recent_ma > older_ma
