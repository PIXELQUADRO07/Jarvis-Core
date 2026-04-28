"""
logger.py — Sistema di logging centralizzato per JARVIS
"""
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

# Crea logger
logger = logging.getLogger("jarvis")
logger.setLevel(logging.DEBUG)

# Handler per file con data
log_file = LOG_DIR / f"jarvis_{datetime.now().strftime('%Y%m%d')}.log"
fh = logging.FileHandler(log_file)
fh.setLevel(logging.DEBUG)

# Handler per console (solo warn e err)
ch = logging.StreamHandler()
ch.setLevel(logging.WARNING)

# Formatter
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
fh.setFormatter(formatter)
ch.setFormatter(formatter)

logger.addHandler(fh)
logger.addHandler(ch)

def debug(msg: str, **kwargs):
    """Log debug message"""
    logger.debug(msg, extra=kwargs)

def info(msg: str, **kwargs):
    """Log info message"""
    logger.info(msg, extra=kwargs)

def warning(msg: str, **kwargs):
    """Log warning message"""
    logger.warning(msg, extra=kwargs)

def error(msg: str, exc: Optional[Exception] = None, **kwargs):
    """Log error message"""
    if exc:
        logger.exception(msg, extra=kwargs)
    else:
        logger.error(msg, extra=kwargs)

def critical(msg: str, exc: Optional[Exception] = None, **kwargs):
    """Log critical message"""
    if exc:
        logger.critical(msg, extra=kwargs, exc_info=True)
    else:
        logger.critical(msg, extra=kwargs)

def get_logger():
    """Ritorna il logger globale"""
    return logger
