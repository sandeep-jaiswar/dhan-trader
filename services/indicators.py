"""
Technical indicator calculation utilities.
Implements all indicators needed for scoring and signal generation.
"""

from typing import List, Dict, Any

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
        rs = avg_gain / avg_loss if avg_loss != 0 else 0
        rsi_values.append(100 - 100 / (1 + rs))
        for delta in deltas[period:]:
            gain = max(delta, 0)
            loss = -min(delta, 0)
            avg_gain = (avg_gain * (period - 1) + gain) / period
            avg_loss = (avg_loss * (period - 1) + loss) / period
            rs = avg_gain / avg_loss if avg_loss != 0 else 0
            rsi_values.append(100 - 100 / (1 + rs))
        return rsi_values

    # Add similar methods for MFI, OBV, VWAP, A/D, candlesticks, etc.
