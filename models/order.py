"""
Order dataclass - represents an order sent to broker.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional

class OrderStatus(str, Enum):
    PENDING = "pending"
    PLACED = "placed"
    PARTIAL = "partial"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"

@dataclass
class Order:
    order_id: str
    symbol: str
    entry_price: float
    quantity: int
    target_price: float
    stop_loss_price: float
    status: OrderStatus
    placed_timestamp: datetime
    filled_timestamp: Optional[datetime] = None
    filled_price: Optional[float] = None
    filled_quantity: Optional[int] = None

    def to_dict(self) -> dict:
        d = {
            **self.__dict__,
            "status": self.status.value
        }
        if self.placed_timestamp:
            d["placed_timestamp"] = self.placed_timestamp.isoformat()
        if self.filled_timestamp:
            d["filled_timestamp"] = self.filled_timestamp.isoformat()
        return d

    @classmethod
    def from_dict(cls, d: dict):
        d = dict(d)
        d["status"] = OrderStatus(d["status"])
        d["placed_timestamp"] = datetime.fromisoformat(d["placed_timestamp"])
        if d.get("filled_timestamp"):
            d["filled_timestamp"] = datetime.fromisoformat(d["filled_timestamp"])
        return cls(**d)

    def cache_key(self) -> str:
        return f"order:{self.order_id}"
