"""Shared numbering inspector utilities used by CLI and trackers."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

from lxml import etree

from .logging_utils import build_emitter
from .model import (
    NumberingResult,
    ParagraphData,
    build_numbering_maps,
    build_paragraphs,
    normalize_glyphs,
)
from .parser import parse_docx_parts
from .renderer import NumberingSession, walk_paragraphs

__all__ = [
    "NumberingInspector",
    "NumberingResult",
    "ParagraphData",
    "build_numbering_maps",
    "build_paragraphs",
    "normalize_glyphs",
    "parse_docx_parts",
    "NumberingSession",
    "walk_paragraphs",
]


class NumberingInspector:
    """High-level façade that reuses the shared numbering helpers."""

    def __init__(
        self,
        *,
        doc_tree: etree._ElementTree,
        num_tree: etree._ElementTree | None,
        styles_tree: etree._ElementTree,
        enable_logging: bool | None = None,
    ) -> None:
        self._doc_tree = doc_tree
        self._num_tree = num_tree  # May be None if document has no numbering.xml
        self._styles_tree = styles_tree
        self._nums = None
        self._abstracts = None
        self._style_numpr = None
        self._session: NumberingSession | None = None
        self._session_debug: bool | None = None
        self._logging_enabled = enable_logging

    @classmethod
    def from_docx(cls, docx_path: Path) -> "NumberingInspector":
        doc_tree, num_tree, styles_tree = parse_docx_parts(docx_path)
        return cls(doc_tree=doc_tree, num_tree=num_tree, styles_tree=styles_tree)

    def ensure_models(self) -> None:
        if self._nums is None or self._abstracts is None or self._style_numpr is None:
            nums, abstracts, style_numpr = build_numbering_maps(
                self._num_tree, self._styles_tree
            )
            self._nums = nums
            self._abstracts = abstracts
            self._style_numpr = style_numpr

    def paragraphs(self) -> Iterable[ParagraphData]:
        return build_paragraphs(self._doc_tree)

    def create_session(self, *, debug: bool = False, logging_enabled: bool | None = None) -> NumberingSession:
        """Return a session suitable for incremental paragraph processing."""
        self.ensure_models()
        assert self._nums is not None
        assert self._abstracts is not None
        assert self._style_numpr is not None
        emitter = build_emitter(logging_enabled if logging_enabled is not None else self._logging_enabled)
        return NumberingSession(
            self._nums,
            self._abstracts,
            self._style_numpr,
            debug=debug,
            log_event=emitter,
        )

    def reset(self) -> None:
        """Reset cached session state without reloading XML."""
        self._session = None
        self._session_debug = None

    def reset_for_attachment(self) -> None:
        """Attachment boundaries do not affect inspector state (no-op)."""
        return None

    def process_paragraph(self, para: ParagraphData, *, debug: bool = False) -> NumberingResult:
        """Process a single paragraph, creating a session on first use."""
        if self._session is None or self._session_debug != debug:
            self._session = self.create_session(debug=debug)
            self._session_debug = debug
        return self._session.process_paragraph(para)

    def analyze(self, debug: bool = False, *, logging_enabled: bool | None = None):
        """Return (rows, debug_rows) for all document paragraphs."""
        rows = []
        debug_rows = []
        session = self.create_session(debug=debug, logging_enabled=logging_enabled)
        for para in build_paragraphs(self._doc_tree):
            result = session.process_paragraph(para)
            rows.append(result.row)
            if debug and result.debug_row:
                debug_rows.append(result.debug_row)
        return rows, debug_rows

    def style_has_numbering(self, style_id: str) -> bool:
        """Return ``True`` when the style maps to numbering metadata."""
        if not style_id:
            return False
        self.ensure_models()
        assert self._style_numpr is not None
        return style_id in self._style_numpr
