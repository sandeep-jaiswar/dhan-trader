"""
Strategy engine for entry/exit signal detection using indicator scores.
"""

from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class StrategyEngine:
    @staticmethod
    def compute_score(features: Dict[str, Any]) -> int:
        """Compute confirmation score (0-12) from feature booleans.

        The function treats missing keys as False. Modify weights here to tune
        scoring behavior.
        """
        score = 0
        # Defensive access: treat any truthy value as a positive signal
        if bool(features.get("obv_bullish")):
            score += 3
        if bool(features.get("rsi_bullish")):
            score += 2
        if bool(features.get("mfi_bullish")):
            score += 2
        if bool(features.get("market_structure")):
            score += 1
        if bool(features.get("candlestick_bullish")):
            score += 1
        if bool(features.get("not_falling")):
            score += 2
        if bool(features.get("htf_uptrend")):
            score += 1

        logger.debug("Computed score=%d from features=%s", score, features)
        return int(score)

    @staticmethod
    def detect_long_signal(features: Dict[str, Any]) -> bool:
        """Return True when conditions indicate a long entry should be taken.

        Current rule: score >= 6 and not_falling and ema_trend.
        """
        try:
            score = StrategyEngine.compute_score(features)
            cond_not_falling = bool(features.get("not_falling"))
            cond_ema_trend = bool(features.get("ema_trend"))
            result = (score >= 6) and cond_not_falling and cond_ema_trend
            logger.debug("detect_long_signal -> score=%s, not_falling=%s, ema_trend=%s => %s",
                         score, cond_not_falling, cond_ema_trend, result)
            return result
        except Exception as e:
            logger.exception("Error while detecting long signal: %s", e)
            return False
