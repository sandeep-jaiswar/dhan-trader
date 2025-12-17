"""
ScanStats dataclass - summary of daily scan stats/results.
"""

from dataclasses import dataclass
from datetime import datetime

@dataclass
class ScanStats:
    scan_date: str
    scan_time: datetime
    total_stocks_scanned: int
    signals_found: int
    orders_placed: int
    orders_failed: int
    scan_duration_seconds: float
    errors: int = 0

    def cache_key(self) -> str:
        return f"scan:{self.scan_date}"
