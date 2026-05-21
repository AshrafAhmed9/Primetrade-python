from __future__ import annotations

import hashlib
import hmac
import logging
import time
import urllib.parse
import uuid
from decimal import Decimal
from typing import Optional

import requests

from .config import (
    BASE_URL,
    BINANCE_ERROR_MESSAGES,
    MAX_RETRIES,
    RECV_WINDOW,
    REQUEST_TIMEOUT,
    RETRY_BACKOFF_BASE,
    USER_AGENT,
)
from .exceptions import BinanceAPIError, NetworkError
from .logging_config import redact_sensitive

logger = logging.getLogger("trading_bot.client")


class BinanceFuturesClient:
    def __init__(self, api_key: str, api_secret: str):
        self._api_secret = api_secret
        self.session = requests.Session()
        self.session.headers.update(
            {
                "X-MBX-APIKEY": api_key,
                "Content-Type": "application/x-www-form-urlencoded",
                "User-Agent": USER_AGENT,
            }
        )

    def _sign(self, params: dict) -> dict:
        params["timestamp"] = int(time.time() * 1000)
        params["recvWindow"] = RECV_WINDOW
        query_string = urllib.parse.urlencode(params)
        signature = hmac.new(
            self._api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        params["signature"] = signature
        return params

    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[dict] = None,
        signed: bool = True,
    ) -> dict:
        params = params or {}
        if signed:
            params = self._sign(params)

        url = BASE_URL + endpoint
        request_id = uuid.uuid4().hex[:8]
        logger.debug("[%s] %s %s params=%s", request_id, method, endpoint, redact_sensitive(params))

        last_exc: Exception = RuntimeError("No attempts made")
        for attempt in range(MAX_RETRIES):
            if attempt > 0:
                backoff = RETRY_BACKOFF_BASE * (2 ** (attempt - 1))
                logger.debug("[%s] Retry %d after %.1fs backoff", request_id, attempt, backoff)
                time.sleep(backoff)
                if signed:
                    params = self._sign(
                        {
                            k: v
                            for k, v in params.items()
                            if k not in ("timestamp", "recvWindow", "signature")
                        }
                    )

            try:
                start = time.perf_counter()
                if method == "GET":
                    response = self.session.get(url, params=params, timeout=REQUEST_TIMEOUT)
                else:
                    response = self.session.post(url, data=params, timeout=REQUEST_TIMEOUT)
                latency_ms = (time.perf_counter() - start) * 1000

                body = response.text[:500]
                logger.debug(
                    "[%s] status=%d latency=%.0fms body=%s",
                    request_id,
                    response.status_code,
                    latency_ms,
                    body,
                )

                if response.status_code != 200:
                    try:
                        data = response.json()
                        error_code = data.get("code", 0)
                        error_msg = BINANCE_ERROR_MESSAGES.get(
                            error_code, data.get("msg", "Unknown error")
                        )
                    except Exception:
                        error_code = 0
                        error_msg = response.text
                    logger.error(
                        "[%s] Binance API error %d: [%d] %s",
                        request_id,
                        response.status_code,
                        error_code,
                        error_msg,
                    )
                    raise BinanceAPIError(response.status_code, error_code, error_msg)

                return response.json()

            except BinanceAPIError:
                raise
            except (requests.ConnectionError, requests.Timeout) as e:
                logger.warning("[%s] Network error on attempt %d: %s", request_id, attempt + 1, e)
                last_exc = e

        logger.error("[%s] All %d retries exhausted", request_id, MAX_RETRIES)
        raise NetworkError(f"Failed after {MAX_RETRIES} retries: {last_exc}") from last_exc

    def place_order(self, order_params: dict) -> dict:
        return self._request("POST", "/fapi/v1/order", params=order_params)

    def get_account_info(self) -> dict:
        return self._request("GET", "/fapi/v2/account")

    def get_price(self, symbol: str) -> Decimal:
        data = self._request(
            "GET", "/fapi/v1/ticker/price", params={"symbol": symbol}, signed=False
        )
        return Decimal(data["price"])

    def check_clock_skew(self) -> None:
        data = self._request("GET", "/fapi/v1/time", signed=False)
        server_time = data["serverTime"]
        local_time = int(time.time() * 1000)
        drift_ms = abs(local_time - server_time)
        if drift_ms > 2000:
            logger.warning(
                "Clock skew detected: %dms drift. Consider syncing your system clock.", drift_ms
            )
        else:
            logger.debug("Clock skew: %dms (OK)", drift_ms)
