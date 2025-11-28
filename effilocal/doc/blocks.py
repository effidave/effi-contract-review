"""Lightweight block value objects used for optional typing experiments."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, Optional


__all__ = ["ParagraphBlock", "TableCellBlock"]


@dataclass(slots=True)
class ParagraphBlock:
    """Structured representation of a paragraph or heading block."""

    id: str
    type: str
    content_hash: str
    text: str
    style: str
    level: Optional[int]
    section_id: str
    indent: Dict[str, int]
    para_id: str = ""
    style_id: str = ""
    num_pr: Optional[Dict[str, Any]] = None
    list: Optional[Dict[str, Any]] = None
    table: Optional[Dict[str, Any]] = None
    anchor: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    restart_group_id: Optional[str] = None
    heading: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Return a dictionary representation compatible with legacy callers."""

        return asdict(self)


@dataclass(slots=True)
class TableCellBlock:
    """Structured representation of a table cell block."""

    id: str
    type: str
    content_hash: str
    text: str
    style: str
    level: Optional[int]
    section_id: str
    table: Dict[str, Any]
    indent: Optional[Dict[str, int]] = None
    list: Optional[Dict[str, Any]] = None
    anchor: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    restart_group_id: Optional[str] = None
    heading: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Return a dictionary representation compatible with legacy callers."""

        return asdict(self)
