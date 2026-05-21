from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from typing import Optional

from .exceptions import ValidationError
from .models import OrderRequest, OrderType, Side

SYMBOL_REGEX = re.compile(r"^[A-Z0-9]{5,20}$")


def validate_symbol(symbol: str) -> str:
    val = symbol.strip().upper()
    if not SYMBOL_REGEX.match(val):
        raise ValueError(
            f"Symbol must be 5-20 uppercase letters/digits (e.g. BTCUSDT), got: '{symbol}'"
        )
    return val


def validate_side(side: str) -> Side:
    val = side.strip().upper()
    try:
        return Side(val)
    except ValueError:
        raise ValueError(f"Side must be one of {[s.value for s in Side]}, got: '{side}'")


def validate_order_type(order_type: str) -> OrderType:
    val = order_type.strip().upper()
    try:
        return OrderType(val)
    except ValueError:
        raise ValueError(
            f"Order type must be one of {[t.value for t in OrderType]}, got: '{order_type}'"
        )


def validate_quantity(quantity: str) -> Decimal:
    try:
        val = Decimal(quantity)
    except InvalidOperation:
        raise ValueError(f"Quantity must be a positive number, got: '{quantity}'")
    if val <= 0:
        raise ValueError(f"Quantity must be greater than zero, got: '{quantity}'")
    return val


def validate_price(price: Optional[str], order_type: OrderType) -> Optional[Decimal]:
    if order_type == OrderType.LIMIT:
        if price is None:
            raise ValueError("--price is required for LIMIT orders")
        try:
            val = Decimal(price)
        except InvalidOperation:
            raise ValueError(f"Price must be a positive number, got: '{price}'")
        if val <= 0:
            raise ValueError(f"Price must be greater than zero, got: '{price}'")
        return val
    if price is not None:
        raise ValueError(f"--price must not be provided for {order_type.value} orders")
    return None


def validate_stop_price(stop_price: Optional[str], order_type: OrderType) -> Optional[Decimal]:
    if order_type == OrderType.STOP:
        if stop_price is None:
            raise ValueError("--stop-price is required for STOP orders")
        try:
            val = Decimal(stop_price)
        except InvalidOperation:
            raise ValueError(f"Stop price must be a positive number, got: '{stop_price}'")
        if val <= 0:
            raise ValueError(f"Stop price must be greater than zero, got: '{stop_price}'")
        return val
    if stop_price is not None:
        raise ValueError("--stop-price must not be provided for MARKET and LIMIT orders")
    return None


def validate_all(
    symbol: str,
    side: str,
    order_type: str,
    quantity: str,
    price: Optional[str],
    stop_price: Optional[str],
) -> OrderRequest:
    errors: list[str] = []
    parsed_symbol = parsed_side = parsed_type = parsed_qty = parsed_price = parsed_stop = None

    for fn, args in [
        (validate_symbol, (symbol,)),
        (validate_side, (side,)),
        (validate_order_type, (order_type,)),
        (validate_quantity, (quantity,)),
    ]:
        try:
            result = fn(*args)
            if fn == validate_symbol:
                parsed_symbol = result
            elif fn == validate_side:
                parsed_side = result
            elif fn == validate_order_type:
                parsed_type = result
            elif fn == validate_quantity:
                parsed_qty = result
        except ValueError as e:
            errors.append(str(e))

    resolved_type = parsed_type or OrderType.MARKET
    try:
        parsed_price = validate_price(price, resolved_type)
    except ValueError as e:
        errors.append(str(e))

    try:
        parsed_stop = validate_stop_price(stop_price, resolved_type)
    except ValueError as e:
        errors.append(str(e))

    if errors:
        raise ValidationError(errors)

    return OrderRequest(
        symbol=parsed_symbol,
        side=parsed_side,
        order_type=parsed_type,
        quantity=parsed_qty,
        price=parsed_price,
        stop_price=parsed_stop,
    )
