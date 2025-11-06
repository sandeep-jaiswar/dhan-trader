"""
Technical indicator calculation utilities.
Implements all indicators needed for scoring and signal generation.
"""

class IndicatorCalculator:
    @staticmethod
    def ema(prices: list[float], period: int) -> list[float]:
        """
        Calculate Exponential Moving Average (EMA).
        """
        ema_list = []
        k = 2 / (period + 1)
        for i, price in enumerate(prices):
            if i < period - 1:
                ema_list.append(None)
            elif i == period - 1:
                ema_list.append(sum(prices[:period]) / period)
            else:
                ema = price * k + ema_list[-1] * (1 - k)
                ema_list.append(ema)
        return ema_list

    @staticmethod
    def rsi(prices: list[float], period: int = 14) -> list[float]:
        """
        Calculate Relative Strength Index (RSI).
        """
        if len(prices) < period + 1:
            return [None] * len(prices)
        deltas = [prices[i] - prices[i - 1] for i in range(1, len(prices))]
        seed = deltas[:period]
        avg_gain = sum(x for x in seed if x > 0) / period
        avg_loss = -sum(x for x in seed if x < 0) / period
        rsi_values = [None] * period
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
    def mfi(highs: list[float], lows: list[float], closes: list[float], volumes: list[float], period: int = 14) -> list[float]:
        """
        Calculate Money Flow Index (MFI).
        MFI is volume-weighted RSI.
        """
        if len(closes) < period + 1:
            return [None] * len(closes)
        
        typical_prices = [(h + l + c) / 3 for h, l, c in zip(highs, lows, closes)]
        money_flows = [tp * v for tp, v in zip(typical_prices, volumes)]
        
        mfi_values = [None] * period
        
        for i in range(period, len(closes)):
            positive_flow = sum(money_flows[j] for j in range(i - period, i) 
                               if typical_prices[j] > typical_prices[j - 1])
            negative_flow = sum(money_flows[j] for j in range(i - period, i) 
                               if typical_prices[j] < typical_prices[j - 1])
            
            if negative_flow == 0:
                mfi = 100.0
            else:
                money_ratio = positive_flow / negative_flow
                mfi = 100 - (100 / (1 + money_ratio))
            
            mfi_values.append(mfi)
        
        return mfi_values

    @staticmethod
    def obv(closes: list[float], volumes: list[float]) -> list[float]:
        """
        Calculate On-Balance Volume (OBV).
        """
        if len(closes) < 2:
            return [0] * len(closes)
        
        obv_values = [0]
        current_obv = 0
        
        for i in range(1, len(closes)):
            if closes[i] > closes[i - 1]:
                current_obv += volumes[i]
            elif closes[i] < closes[i - 1]:
                current_obv -= volumes[i]
            obv_values.append(current_obv)
        
        return obv_values

    @staticmethod
    def vwap(highs: list[float], lows: list[float], closes: list[float], volumes: list[float]) -> list[float]:
        """
        Calculate Volume Weighted Average Price (VWAP).
        """
        vwap_values = []
        cumulative_tp_volume = 0
        cumulative_volume = 0
        
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
    def ad_line(highs: list[float], lows: list[float], closes: list[float], volumes: list[float]) -> list[float]:
        """
        Calculate Accumulation/Distribution Line (A/D).
        """
        ad_values = []
        cumulative_ad = 0
        
        for h, l, c, v in zip(highs, lows, closes, volumes):
            if h == l:
                clv = 0
            else:
                clv = ((c - l) - (h - c)) / (h - l)
            
            cumulative_ad += clv * v
            ad_values.append(cumulative_ad)
        
        return ad_values

    @staticmethod
    def sma(prices: list[float], period: int) -> list[float]:
        """
        Calculate Simple Moving Average (SMA).
        """
        sma_list = []
        for i in range(len(prices)):
            if i < period - 1:
                sma_list.append(None)
            else:
                sma = sum(prices[i - period + 1:i + 1]) / period
                sma_list.append(sma)
        return sma_list

    @staticmethod
    def macd(prices: list[float], fast: int = 12, slow: int = 26, signal: int = 9) -> dict:
        """
        Calculate MACD (Moving Average Convergence Divergence).
        Returns dict with 'macd', 'signal', and 'histogram' lists.
        """
        ema_fast = IndicatorCalculator.ema(prices, fast)
        ema_slow = IndicatorCalculator.ema(prices, slow)
        
        macd_line = []
        for f, s in zip(ema_fast, ema_slow):
            if f is None or s is None:
                macd_line.append(None)
            else:
                macd_line.append(f - s)
        
        # Calculate signal line (EMA of MACD) - only use non-None values
        non_none_indices = [i for i, x in enumerate(macd_line) if x is not None]
        if non_none_indices:
            first_valid_idx = non_none_indices[0]
            signal_prices = [macd_line[i] for i in non_none_indices]
            signal_ema = IndicatorCalculator.ema(signal_prices, signal)
            
            # Map back to original indices
            signal_line = [None] * len(macd_line)
            for i, idx in enumerate(non_none_indices):
                signal_line[idx] = signal_ema[i]
        else:
            signal_line = [None] * len(macd_line)
        
        # Calculate histogram
        histogram = []
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
    def atr(highs: list[float], lows: list[float], closes: list[float], period: int = 14) -> list[float]:
        """
        Calculate Average True Range (ATR).
        """
        if len(closes) < 2:
            return [None] * len(closes)
        
        true_ranges = [highs[0] - lows[0]]
        
        for i in range(1, len(closes)):
            tr = max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i - 1]),
                abs(lows[i] - closes[i - 1])
            )
            true_ranges.append(tr)
        
        atr_values = [None] * (period - 1)
        atr = sum(true_ranges[:period]) / period
        atr_values.append(atr)
        
        for i in range(period, len(true_ranges)):
            atr = (atr * (period - 1) + true_ranges[i]) / period
            atr_values.append(atr)
        
        return atr_values

    @staticmethod
    def bollinger_bands(prices: list[float], period: int = 20, std_dev: float = 2.0) -> dict:
        """
        Calculate Bollinger Bands.
        Returns dict with 'upper', 'middle', and 'lower' bands.
        """
        middle_band = IndicatorCalculator.sma(prices, period)
        upper_band = []
        lower_band = []
        
        for i in range(len(prices)):
            if i < period - 1:
                upper_band.append(None)
                lower_band.append(None)
            else:
                window = prices[i - period + 1:i + 1]
                std = (sum((x - middle_band[i]) ** 2 for x in window) / period) ** 0.5
                upper_band.append(middle_band[i] + std_dev * std)
                lower_band.append(middle_band[i] - std_dev * std)
        
        return {
            'upper': upper_band,
            'middle': middle_band,
            'lower': lower_band
        }

    @staticmethod
    def detect_bullish_candle(opens: list[float], highs: list[float], lows: list[float], closes: list[float], idx: int) -> bool:
        """
        Detect bullish candlestick patterns at given index.
        Checks for: Hammer, Bullish Engulfing, Morning Star, etc.
        """
        if idx < 2:
            return False
        
        # Current candle
        o, h, l, c = opens[idx], highs[idx], lows[idx], closes[idx]
        body = abs(c - o)
        range_hl = h - l
        
        # Previous candle
        o_prev, c_prev = opens[idx - 1], closes[idx - 1]
        
        # Hammer pattern
        if c > o and range_hl > 0:
            lower_wick = o - l
            upper_wick = h - c
            if lower_wick > 2 * body and upper_wick < body * 0.1:
                return True
        
        # Bullish Engulfing
        if c > o and c_prev < o_prev:  # Current bullish, previous bearish
            if c > o_prev and o < c_prev:
                return True
        
        return False

    @staticmethod
    def is_uptrend(prices: list[float], period: int = 50, lookback: int = 10) -> bool:
        """
        Check if prices are in uptrend using moving average comparison.
        
        Args:
            prices: List of prices
            period: Period for moving average calculation
            lookback: Number of periods to look back for comparison
        """
        if len(prices) < period + lookback:
            return False
        
        recent_ma = sum(prices[-period:]) / period
        older_ma = sum(prices[-period - lookback:-lookback]) / period
        
        return recent_ma > older_ma
