from __future__ import annotations

BASE_URL = "https://testnet.binancefuture.com"
RECV_WINDOW = 5000
REQUEST_TIMEOUT = 10
MAX_RETRIES = 3
RETRY_BACKOFF_BASE = 0.5
LOG_DIR = "logs"
LOG_FILE = "logs/trading_bot.log"
TRADES_FILE = "logs/trades.jsonl"
LOG_MAX_BYTES = 1_000_000
LOG_BACKUP_COUNT = 3
VERSION = "1.0.0"
USER_AGENT = f"trading-bot/{VERSION}"

BINANCE_ERROR_MESSAGES: dict[int, str] = {
    -1121: "Invalid symbol. Verify it exists on Binance Futures (e.g. BTCUSDT).",
    -1102: "Required parameter missing.",
    -2019: "Insufficient margin. Add funds to your testnet account.",
    -1111: "Price/quantity precision exceeds maximum allowed.",
    -1100: "Illegal characters in parameter.",
    -4061: "Order side does not match position side.",
}
