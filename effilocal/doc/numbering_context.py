"""Shared numbering context/event models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Any


@dataclass(frozen=True)
class NumberingEvent:
    """Immutable snapshot of numbering metadata for a block."""

    block_id: str
    payload: Mapping[str, Any]
    restart_group_id: str | None
