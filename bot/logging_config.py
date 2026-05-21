import logging
import os
from logging.handlers import RotatingFileHandler

from .config import LOG_DIR, LOG_FILE, LOG_MAX_BYTES, LOG_BACKUP_COUNT


def setup_logging() -> logging.Logger:
    os.makedirs(LOG_DIR, exist_ok=True)

    fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
    )

    file_handler = RotatingFileHandler(
        LOG_FILE, maxBytes=LOG_MAX_BYTES, backupCount=LOG_BACKUP_COUNT
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(fmt)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.WARNING)
    stream_handler.setFormatter(fmt)

    logger = logging.getLogger("trading_bot")
    logger.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    logger.propagate = False

    return logger


def redact_sensitive(params: dict) -> dict:
    redacted = dict(params)
    for key in ("apiKey", "api_key", "signature"):
        if key in redacted:
            val = str(redacted[key])
            redacted[key] = val[:8] + "***" if len(val) > 8 else "***"
    for key in ("secret", "apiSecret"):
        if key in redacted:
            redacted[key] = "***"
    return redacted
