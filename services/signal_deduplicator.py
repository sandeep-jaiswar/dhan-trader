"""
Signal deduplication service.
Prevents duplicate signals/order placements for same stock/day.
"""

from utils.cache import cache
from models.signal import Signal

class SignalDeduplicator:
    DUPLICATE_CHECK_HOURS = 24

    @staticmethod
    def is_duplicate(signal: Signal) -> bool:
        cache_key = f"dup:{signal.symbol}:{signal.detected_date}"
        existing = cache.get(cache_key)
        return bool(existing and existing.get("hash"))

    @staticmethod
    def mark_processed(signal: Signal) -> bool:
        from hashlib import md5
        key_str = f"{signal.symbol}_{signal.detected_date}_{signal.entry_price}"
        signal_hash = md5(key_str.encode()).hexdigest()
        cache_key = f"dup:{signal.symbol}:{signal.detected_date}"
        data = {"hash": signal_hash, "processed_time": signal.signal_timestamp.isoformat()}
        cache.set(cache_key, data, ttl_hours=SignalDeduplicator.DUPLICATE_CHECK_HOURS)
        return True
