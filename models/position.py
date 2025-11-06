"""
Position dataclass - tracks open/finalized trades in portfolio.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Position:
    symbol: str
    entry_price: float
    entry_time: datetime
    quantity: int = 1
    target_price: Optional[float] = None
    stop_loss_price: Optional[float] = None
    current_price: Optional[float] = None
    status: str = "active"         # active/closed
    pnl: Optional[float] = None
    pnl_percentage: Optional[float] = None

    def update_price(self, price: float):
        self.current_price = price
        self.pnl = (price - self.entry_price) * self.quantity
        self.pnl_percentage = ((price - self.entry_price) / self.entry_price) * 100 if self.entry_price else None

    def close(self, exit_price: float):
        self.status = "closed"
        self.update_price(exit_price)
