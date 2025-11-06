"""
Strategy engine for entry/exit signal detection using indicator scores.
"""

from typing import Dict, Any
from services.indicators import IndicatorCalculator

class StrategyEngine:
    @staticmethod
    def compute_score(features: Dict[str, Any]) -> int:
        """
        Compute confirmationScore (0-12) as per roadmap scoring.
        """
        score = 0
        # Example logic (customize as per roadmap)
        if features.get("obv_bullish"):
            score += 3
        if features.get("rsi_bullish"):
            score += 2
        if features.get("mfi_bullish"):
            score += 2
        if features.get("market_structure"):
            score += 1
        if features.get("candlestick_bullish"):
            score += 1
        if features.get("not_falling"):
            score += 2
        if features.get("htf_uptrend"):
            score += 1
        return score

    @staticmethod
    def detect_long_signal(features: Dict[str, Any]) -> bool:
        """
        Detect if long entry should trigger.
        """
        score = StrategyEngine.compute_score(features)
        if score >= 6 and features.get("not_falling") and features.get("ema_trend"):
            return True
        return False
