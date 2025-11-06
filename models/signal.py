"""
Signal dataclass - represents a detected entry in a stock.
"""

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional

@dataclass
class Signal:
    symbol: str
    entry_price: float
    stop_loss: float
    take_profit: float
    confirmation_score: int     # 0-12
    signal_timestamp: datetime
    detected_date: str          # "YYYY-MM-DD"
    ema_21: Optional[float] = None
    ema_50: Optional[float] = None
    rsi: Optional[float] = None
    mfi: Optional[float] = None
    obv: Optional[float] = None
    strategy_version: str = "1.0"
    notes: Optional[str] = None

    def to_dict(self) -> dict:
        d = asdict(self)
        d['signal_timestamp'] = self.signal_timestamp.isoformat()
        return d

    @classmethod
    def from_dict(cls, d: dict):
        d = dict(d)
        d['signal_timestamp'] = datetime.fromisoformat(d['signal_timestamp'])
        return cls(**d)

    def cache_key(self) -> str:
        return f"signal:{self.symbol}:{self.detected_date}:{int(self.signal_timestamp.timestamp())}"
