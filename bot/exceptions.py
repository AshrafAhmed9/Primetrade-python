from __future__ import annotations

class TradingBotError(Exception):
    """Base for all trading bot errors."""


class ValidationError(TradingBotError):
    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__("\n".join(errors))


class AuthenticationError(TradingBotError):
    """Missing or rejected API credentials."""


class BinanceAPIError(TradingBotError):
    def __init__(self, status_code: int, error_code: int, error_msg: str):
        self.status_code = status_code
        self.error_code = error_code
        self.error_msg = error_msg
        super().__init__(f"HTTP {status_code}: [{error_code}] {error_msg}")


class NetworkError(TradingBotError):
    """Connection or timeout failures."""
