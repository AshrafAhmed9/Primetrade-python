from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Optional


class Side(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"


class TimeInForce(str, Enum):
    GTC = "GTC"


@dataclass
class OrderRequest:
    symbol: str
    side: Side
    order_type: OrderType
    quantity: Decimal
    price: Optional[Decimal] = None
    stop_price: Optional[Decimal] = None

    def to_api_params(self) -> dict:
        params = {
            "symbol": self.symbol,
            "side": self.side.value,
            "type": self.order_type.value,
            "quantity": f"{self.quantity:.3f}",
        }
        if self.order_type == OrderType.LIMIT:
            params["timeInForce"] = TimeInForce.GTC.value
            params["price"] = f"{self.price:.2f}"
        if self.order_type == OrderType.STOP:
            params["type"] = "STOP_MARKET"
            params["stopPrice"] = f"{self.stop_price:.2f}"
        return params
