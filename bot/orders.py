from __future__ import annotations

import json
import logging
import os
import time
from datetime import datetime, timezone
from decimal import Decimal

from rich.table import Table

from .client import BinanceFuturesClient
from .config import TRADES_FILE
from .models import OrderRequest, OrderType, Side

logger = logging.getLogger("trading_bot.orders")


def place_order(client: BinanceFuturesClient, req: OrderRequest) -> dict:
    params = req.to_api_params()
    logger.info(
        "Placing %s %s order: %s qty=%s price=%s",
        req.order_type.value, req.side.value, req.symbol, req.quantity, req.price,
    )
    response = client.place_order(params)
    logger.info(
        "Order accepted: orderId=%s status=%s",
        response.get("orderId"), response.get("status"),
    )
    _log_trade(req, response)
    return response


def place_stop_order(
    client: BinanceFuturesClient,
    req: OrderRequest,
    timeout: int = 60,
    poll_interval: float = 1.0,
) -> dict:
    """Monitors live price and fires a MARKET order when stop price is hit.
    BUY STOP  triggers when price rises  >= stop_price.
    SELL STOP triggers when price falls  <= stop_price.
    """
    stop_price = req.stop_price
    deadline = time.time() + timeout
    current_price = Decimal("0")

    logger.info(
        "Watching %s for %s STOP at stop_price=%s (timeout=%ds)",
        req.symbol, req.side.value, stop_price, timeout,
    )

    while time.time() < deadline:
        current_price = client.get_price(req.symbol)
        triggered = (
            (req.side == Side.BUY and current_price >= stop_price) or
            (req.side == Side.SELL and current_price <= stop_price)
        )
        logger.debug("price=%s stop=%s triggered=%s", current_price, stop_price, triggered)
        if triggered:
            logger.info(
                "STOP triggered: price=%s crossed stop=%s", current_price, stop_price
            )
            break
        time.sleep(poll_interval)
    else:
        raise TimeoutError(
            f"Stop not triggered within {timeout}s. Last price: {current_price}"
        )

    market_req = OrderRequest(
        symbol=req.symbol,
        side=req.side,
        order_type=OrderType.MARKET,
        quantity=req.quantity,
    )
    response = client.place_order(market_req.to_api_params())
    logger.info(
        "Stop order executed: orderId=%s status=%s",
        response.get("orderId"), response.get("status"),
    )
    _log_trade(req, response)
    return response


def _log_trade(req: OrderRequest, response: dict) -> None:
    os.makedirs(os.path.dirname(TRADES_FILE), exist_ok=True)
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "symbol": req.symbol,
        "side": req.side.value,
        "type": req.order_type.value,
        "quantity": str(req.quantity),
        "price": str(req.price) if req.price else None,
        "stop_price": str(req.stop_price) if req.stop_price else None,
        "orderId": response.get("orderId"),
        "status": response.get("status"),
        "executedQty": response.get("executedQty"),
        "avgPrice": response.get("avgPrice"),
    }
    with open(TRADES_FILE, "a") as f:
        f.write(json.dumps(record) + "\n")


def format_order_summary(req: OrderRequest) -> Table:
    table = Table(title="Order Request Summary", show_header=False, min_width=40)
    table.add_column("Field", style="bold cyan")
    table.add_column("Value")
    table.add_row("Symbol", req.symbol)
    table.add_row("Side", req.side.value)
    table.add_row("Type", req.order_type.value)
    table.add_row("Quantity", str(req.quantity))
    table.add_row("Price", str(req.price) if req.price else "N/A")
    table.add_row("Stop Price", str(req.stop_price) if req.stop_price else "N/A")
    return table


def format_order_response(response: dict) -> Table:
    table = Table(title="Order Response", show_header=False, min_width=40)
    table.add_column("Field", style="bold cyan")
    table.add_column("Value")
    table.add_row("Order ID", str(response.get("orderId", "N/A")))
    table.add_row("Status", response.get("status", "N/A"))
    table.add_row("Symbol", response.get("symbol", "N/A"))
    table.add_row("Side", response.get("side", "N/A"))
    table.add_row("Type", response.get("type", "N/A"))
    table.add_row("Executed Qty", response.get("executedQty", "N/A"))
    table.add_row("Avg Price", response.get("avgPrice", "N/A"))
    return table
