"""
logger.py — Logging strutturato JSON con rotazione automatica
"""
import json
import logging
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)


class JSONFormatter(logging.Formatter):
    """Formatta i log come JSON strutturato."""

    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "ts":      datetime.fromtimestamp(record.created).strftime("%Y-%m-%dT%H:%M:%S"),
            "level":   record.levelname,
            "module":  record.module,
            "msg":     record.getMessage(),
        }
        if record.exc_info:
            log_obj["exc"] = self.formatException(record.exc_info)
        return json.dumps(log_obj, ensure_ascii=False)


def _build_logger() -> logging.Logger:
    lg = logging.getLogger("jarvis")
    if lg.handlers:
        return lg
    lg.setLevel(logging.DEBUG)

    log_file = LOG_DIR / f"jarvis_{datetime.now().strftime('%Y%m%d')}.log"

    # File handler JSON con rotazione (5 MB, 5 backup)
    fh = RotatingFileHandler(
        log_file, maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(JSONFormatter())

    # Console handler solo WARNING+
    ch = logging.StreamHandler(sys.stderr)
    ch.setLevel(logging.WARNING)
    ch.setFormatter(logging.Formatter("%(levelname)s %(message)s"))

    lg.addHandler(fh)
    lg.addHandler(ch)
    return lg


_logger = _build_logger()


def debug(msg: str, **kwargs): _logger.debug(msg)
def info(msg: str, **kwargs):  _logger.info(msg)
def warning(msg: str, **kwargs): _logger.warning(msg)
def error(msg: str, exc: Optional[Exception] = None, **kwargs):
    if exc:
        _logger.exception(msg)
    else:
        _logger.error(msg)
def critical(msg: str, exc: Optional[Exception] = None, **kwargs):
    if exc:
        _logger.critical(msg, exc_info=True)
    else:
        _logger.critical(msg)

def get_logger() -> logging.Logger:
    return _logger
