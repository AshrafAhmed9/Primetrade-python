import pytest
from decimal import Decimal

from bot.exceptions import ValidationError
from bot.models import OrderType, Side
from bot.validators import validate_all


def test_valid_market_order():
    req = validate_all("BTCUSDT", "BUY", "MARKET", "0.001", None, None)
    assert req.symbol == "BTCUSDT"
    assert req.side == Side.BUY
    assert req.order_type == OrderType.MARKET
    assert req.quantity == Decimal("0.001")
    assert req.price is None


def test_valid_limit_order():
    req = validate_all("BTCUSDT", "BUY", "LIMIT", "0.001", "45000", None)
    assert req.price == Decimal("45000")


def test_valid_stop_order():
    req = validate_all("BTCUSDT", "SELL", "STOP", "0.001", None, "44000")
    assert req.stop_price == Decimal("44000")
    assert req.price is None


def test_symbol_lowercase_normalised():
    req = validate_all("btcusdt", "BUY", "MARKET", "0.001", None, None)
    assert req.symbol == "BTCUSDT"


def test_symbol_too_short():
    with pytest.raises(ValidationError) as exc_info:
        validate_all("BT", "BUY", "MARKET", "0.001", None, None)
    assert any("Symbol" in e for e in exc_info.value.errors)


def test_invalid_side():
    with pytest.raises(ValidationError) as exc_info:
        validate_all("BTCUSDT", "HOLD", "MARKET", "0.001", None, None)
    assert any("Side" in e for e in exc_info.value.errors)


def test_negative_quantity():
    with pytest.raises(ValidationError) as exc_info:
        validate_all("BTCUSDT", "BUY", "MARKET", "-1", None, None)
    assert any("Quantity" in e for e in exc_info.value.errors)


def test_limit_missing_price():
    with pytest.raises(ValidationError) as exc_info:
        validate_all("BTCUSDT", "BUY", "LIMIT", "0.001", None, None)
    assert any("price" in e.lower() for e in exc_info.value.errors)


def test_stop_missing_stop_price():
    with pytest.raises(ValidationError) as exc_info:
        validate_all("BTCUSDT", "SELL", "STOP", "0.001", "43500", None)
    assert any("stop-price" in e.lower() for e in exc_info.value.errors)


def test_multiple_errors_collected():
    with pytest.raises(ValidationError) as exc_info:
        validate_all("BT", "HOLD", "MARKET", "-1", None, None)
    assert len(exc_info.value.errors) >= 3
