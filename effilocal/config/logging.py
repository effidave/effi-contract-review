"""Centralized logging configuration for Sprint 1."""

from __future__ import annotations

import logging
from logging import Logger


LOG_FORMAT = "%(levelname)s %(name)s: %(message)s"
DEFAULT_LEVEL = logging.DEBUG


def configure_logging(level: int = DEFAULT_LEVEL) -> None:
    """Configure root logging once."""

    logging.basicConfig(level=level, format=LOG_FORMAT)


def get_logger(name: str) -> Logger:
    """Return a module-level logger."""

    return logging.getLogger(name)
