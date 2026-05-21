
from bot.logging_config import redact_sensitive


def test_redact_sensitive_masks_signature():
    params = {"symbol": "BTCUSDT", "signature": "abcdef1234567890", "timestamp": 123}
    result = redact_sensitive(params)
    assert result["signature"].endswith("***")
    assert result["symbol"] == "BTCUSDT"


def test_redact_sensitive_masks_api_key():
    params = {"apiKey": "ABCDEFGH12345678"}
    result = redact_sensitive(params)
    assert result["apiKey"] == "ABCDEFGH***"


def test_redact_sensitive_short_key():
    params = {"signature": "abc"}
    result = redact_sensitive(params)
    assert result["signature"] == "***"


def test_redact_does_not_mutate_original():
    params = {"signature": "abcdef1234567890"}
    redact_sensitive(params)
    assert params["signature"] == "abcdef1234567890"
