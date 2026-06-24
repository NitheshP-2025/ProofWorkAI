"""
ProofWork AI - Centralized Logger
===================================
Provides a unified, production-grade logging setup for all agents and services.

Features:
  - Console + rotating file handler
  - Structured formatting with timestamps and module names
  - Per-module logger factory
  - Configurable log levels via environment variable

Author: Swetha
Module: utils/logger.py
"""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = LOG_DIR / "proofwork_ai.log"
MAX_BYTES = 5 * 1024 * 1024   # 5 MB per file
BACKUP_COUNT = 3               # Keep 3 rotated backups

LOG_LEVEL_ENV = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_LEVEL = getattr(logging, LOG_LEVEL_ENV, logging.INFO)

# ---------------------------------------------------------------------------
# Formatters
# ---------------------------------------------------------------------------

CONSOLE_FORMAT = (
    "%(asctime)s | %(levelname)-8s | %(name)-30s | %(message)s"
)

FILE_FORMAT = (
    "%(asctime)s | %(levelname)-8s | %(name)-30s | "
    "%(filename)s:%(lineno)d | %(funcName)s() | %(message)s"
)

DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


# ---------------------------------------------------------------------------
# Root Logger Configuration (run once at module import)
# ---------------------------------------------------------------------------

def _configure_root_logger() -> None:
    """Configure the root logger with console and file handlers."""
    root = logging.getLogger("proofwork_ai")
    if root.handlers:
        # Already configured — skip
        return

    root.setLevel(LOG_LEVEL)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(LOG_LEVEL)
    console_handler.setFormatter(
        logging.Formatter(fmt=CONSOLE_FORMAT, datefmt=DATE_FORMAT)
    )

    # Rotating file handler
    try:
        file_handler = RotatingFileHandler(
            LOG_FILE,
            maxBytes=MAX_BYTES,
            backupCount=BACKUP_COUNT,
            encoding="utf-8",
        )
        file_handler.setLevel(logging.DEBUG)  # File always captures DEBUG+
        file_handler.setFormatter(
            logging.Formatter(fmt=FILE_FORMAT, datefmt=DATE_FORMAT)
        )
        root.addHandler(file_handler)
    except (OSError, PermissionError) as exc:
        # If file logging fails (e.g., read-only filesystem), warn but continue
        console_handler.emit(
            logging.LogRecord(
                name="proofwork_ai.logger",
                level=logging.WARNING,
                pathname=__file__,
                lineno=0,
                msg=f"File logging unavailable: {exc}",
                args=(),
                exc_info=None,
            )
        )

    root.addHandler(console_handler)
    root.propagate = False


_configure_root_logger()


# ---------------------------------------------------------------------------
# Public Factory
# ---------------------------------------------------------------------------

def get_logger(name: str) -> logging.Logger:
    """
    Returns a named child logger under the 'proofwork_ai' hierarchy.

    Usage:
        from utils.logger import get_logger
        logger = get_logger(__name__)
        logger.info("Agent started")

    Args:
        name: Typically pass ``__name__`` for automatic module naming.

    Returns:
        A configured logging.Logger instance.
    """
    # Prefix all loggers under the proofwork_ai namespace
    qualified = f"proofwork_ai.{name}" if not name.startswith("proofwork_ai") else name
    return logging.getLogger(qualified)
