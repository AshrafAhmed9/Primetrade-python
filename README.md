# Binance Futures Testnet Trading Bot

![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![Testnet](https://img.shields.io/badge/binance-futures%20testnet-yellow)
![License](https://img.shields.io/badge/license-MIT-green)

> **Testnet only.** This bot is configured exclusively for Binance Futures Testnet. Do not use production API keys.

A lightweight Python CLI for placing orders on Binance Futures Testnet (USDT-M). Built with raw REST calls and HMAC-SHA256 signing — no third-party Binance SDK — to demonstrate direct API integration, structured logging, input validation, and retry resilience.

---

## Features

- **MARKET** and **LIMIT** orders with full validation
- **STOP order (bonus)** — software-monitored: polls live price and fires a MARKET order when the stop price is crossed
- Structured logging with rotating log files and sensitive data redaction
- Exponential backoff retry on network failures
- Per-request tracing IDs for log correlation
- Dry-run mode to preview orders without placing them
- Credential auth check with account balance display and clock skew detection

---

## Prerequisites

- Python 3.8+
- A Binance Futures Testnet account — register at https://testnet.binancefuture.com
- Testnet API Key and Secret (generated from the testnet site — no KYC required)

---

## Setup

### 1. Clone or download the project

```bash
git clone <your-repo-url>
cd trading_bot
```

### 2. Create a virtual environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux / Mac
python -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure credentials

Copy the example env file and fill in your testnet keys:

```bash
# Windows
copy .env.example .env

# Linux / Mac
cp .env.example .env
```

Edit `.env`:

```
BINANCE_API_KEY=your_testnet_api_key_here
BINANCE_API_SECRET=your_testnet_secret_key_here
```

> Keys are read from environment variables only — never from CLI flags — to keep them out of shell history.

---

## Usage

### Verify credentials

```bash
python cli.py --check-auth
```

### Place a MARKET order

```bash
python cli.py --symbol BTCUSDT --side BUY --order-type MARKET --quantity 0.002
```

### Place a LIMIT order

```bash
python cli.py --symbol BTCUSDT --side BUY --order-type LIMIT --quantity 0.002 --price 45000
```

### Place a STOP order (bonus feature)

Monitors the live price and fires a MARKET order when the stop price is crossed.

```bash
# SELL STOP: fires market sell when price drops to or below 44000
python cli.py --symbol BTCUSDT --side SELL --order-type STOP --quantity 0.002 --stop-price 44000

# BUY STOP: fires market buy when price rises to or above 110000
python cli.py --symbol BTCUSDT --side BUY --order-type STOP --quantity 0.002 --stop-price 110000

# Custom watch timeout (default 60s)
python cli.py --symbol BTCUSDT --side SELL --order-type STOP --quantity 0.002 --stop-price 44000 --watch-timeout 120
```

### Dry run (preview without placing)

```bash
python cli.py --symbol BTCUSDT --side BUY --order-type LIMIT --quantity 0.002 --price 45000 --dry-run
```

### All options

```bash
python cli.py --help
```

---

## CLI Reference

| Argument | Required | Description |
|---|---|---|
| `--symbol` | Yes | Trading pair, e.g. `BTCUSDT` |
| `--side` | Yes | `BUY` or `SELL` |
| `--order-type` | Yes | `MARKET`, `LIMIT`, or `STOP` |
| `--quantity` | Yes | Order quantity, e.g. `0.002` |
| `--price` | LIMIT only | Limit price |
| `--stop-price` | STOP only | Stop trigger price |
| `--watch-timeout` | No | Seconds to monitor price for STOP (default: 60) |
| `--check-auth` | No | Verify credentials and show balances |
| `--dry-run` | No | Preview order without placing it |

---

## Sample Output

```
Trading Bot v1.0.0 — Binance Futures Testnet

         Order Request Summary
┌──────────────────────┬───────────────┐
│ Symbol               │ BTCUSDT       │
│ Side                 │ BUY           │
│ Type                 │ LIMIT         │
│ Quantity             │ 0.002         │
│ Price                │ 45000         │
│ Stop Price           │ N/A           │
└──────────────────────┴───────────────┘

Proceed? [y/N]: y

             Order Response
┌────────────────────┬─────────────────┐
│ Order ID           │ 13171440849     │
│ Status             │ NEW             │
│ Symbol             │ BTCUSDT         │
│ Side               │ BUY             │
│ Type               │ LIMIT           │
│ Executed Qty       │ 0.0000          │
│ Avg Price          │ 0.00            │
└────────────────────┴─────────────────┘

✓ Order placed successfully.
Completed in 2.00s
```

---

## Architecture

```
cli.py
  └── validates input          → bot/validators.py
  └── builds OrderRequest      → bot/models.py
  └── routes to order logic    → bot/orders.py
        └── calls HTTP client  → bot/client.py
              └── signs & sends → Binance Futures Testnet API
```

All constants live in `bot/config.py`. Exceptions are defined in `bot/exceptions.py`. Logging is configured once in `bot/logging_config.py`.

---

## Design Principles

| Decision | Reason |
|---|---|
| Raw `requests` + HMAC signing | Demonstrates understanding of the auth protocol directly; avoids SDK version fragility |
| `Decimal` for prices and quantities | Float arithmetic is imprecise; Binance rejects incorrect precision |
| Collect-all validation errors | Users see every problem at once instead of fixing one error per run |
| Retry with exponential backoff | Transient network failures are common in trading; retrying blindly at full speed can cause duplicate orders — backoff prevents that |
| Credentials via env vars only | Keeps secrets out of shell history, process lists, and logs |
| Layered architecture | Each layer has one responsibility; the CLI knows nothing about HTTP, the client knows nothing about CLI |

---

## Logging

- Log file: `logs/trading_bot.log` (rotating, max 1 MB, 3 backups)
- Trade history: `logs/trades.jsonl` (one JSON line per order placed)
- Every request logs a unique 8-character request ID for tracing
- API keys and signatures are redacted in all log output
- File handler: `DEBUG` level (all detail)
- Console: `WARNING` and above only (clean terminal output)

Sample log entry:

```
2026-05-21T13:25:58+0530 | DEBUG    | trading_bot.client | _request:61 | [2bc08cf0] POST /fapi/v1/order params={'symbol': 'BTCUSDT', 'side': 'BUY', ...}
2026-05-21T13:25:58+0530 | DEBUG    | trading_bot.client | _request:84 | [2bc08cf0] status=200 latency=312ms body={"orderId":13171440849,...}
```

---

## Running Tests

```bash
pytest tests/ -v
```

Expected output: 17 tests, all passing.

Tests cover:
- All validator rules including multi-error collection
- `OrderRequest.to_api_params()` for all three order types
- `redact_sensitive()` key masking

---

## Binance Error Reference

| Code | Meaning |
|---|---|
| -1121 | Invalid symbol |
| -1102 | Required parameter missing |
| -2019 | Insufficient margin |
| -1111 | Price/quantity precision too high |
| -1100 | Illegal characters in parameter |
| -4164 | Order notional below minimum ($50) |

---

## Security Notes

- API keys are loaded from environment variables or `.env` file — never passed on the command line
- Keys and signatures are redacted to `ABCD1234***` in all log output
- `.env` is listed in `.gitignore` and will never be committed
- This bot targets the **testnet only** — the base URL is hardcoded to `https://testnet.binancefuture.com`

---

## Future Improvements

- WebSocket market stream for real-time price feed (replaces polling in STOP orders)
- TWAP execution: split large orders into time-weighted slices
- Async order placement with `httpx` for higher throughput
- SQLite trade history with query support
- Position monitoring and PnL display

---

## Exit Codes

| Code | Meaning |
|---|---|
| `0` | Success |
| `1` | Validation error, API error, network failure, or unexpected error |
