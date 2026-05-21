from decimal import Decimal

from bot.models import OrderRequest, OrderType, Side


def _req(order_type, price=None, stop_price=None):
    return OrderRequest(
        symbol="BTCUSDT",
        side=Side.BUY,
        order_type=order_type,
        quantity=Decimal("0.001"),
        price=Decimal(price) if price else None,
        stop_price=Decimal(stop_price) if stop_price else None,
    )


def test_stop_params_uses_stop_market_and_no_price():
    params = _req(OrderType.STOP, stop_price="44000").to_api_params()
    assert params["type"] == "STOP_MARKET"
    assert params["stopPrice"] == "44000.00"
    assert "price" not in params
    assert "timeInForce" not in params



def test_limit_params_has_price_and_tif():
    params = _req(OrderType.LIMIT, price="45000").to_api_params()
    assert params["type"] == "LIMIT"
    assert params["price"] == "45000.00"
    assert params["timeInForce"] == "GTC"
    assert "stopPrice" not in params





def test_quantity_formatted_to_3dp():
    params = _req(OrderType.MARKET).to_api_params()
    assert params["quantity"] == "0.001"
