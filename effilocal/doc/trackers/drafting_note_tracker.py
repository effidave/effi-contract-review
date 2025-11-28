"""Drafting note heuristics shared during parsing."""

from __future__ import annotations

import re
from typing import Any

DRAFTING_NOTE_PATTERN = re.compile(
    r"""
    ^\s*[\(\[\{\\"'\u201c\u2018~]*\s*
    (
      draft(?:ing)?\s+note\b
      |negotiation\s+note\b
      |for\s+negotiation\s+only\b
      |for\s+internal\s+(?:use|discussion)\s+only\b
      |internal\s+note\b
      |note\s+to\b
      |note\s+for\b
      |note\s*[-\u2013\u2014"”]\s*(?:draft|delete|remove|do\s+not|omit|optional|internal|negotiation)
      |note:\s*(?:draft|delete|remove|do\s+not|omit|optional|for\s+negotiation|for\s+internal|internal|negotiation)
    )
    """,
    re.IGNORECASE | re.VERBOSE,
)

DRAFTING_NOTE_NEAR_PATTERN = re.compile(r"draft(?:ing)?\s+note", re.IGNORECASE)

DRAFTING_NOTE_LEADING_WRAPPERS = " \t\u00a0([{\\\"'\u201c\u2018"


class DraftingNoteHelper:
    """Utility for tagging drafting notes."""

    def looks_like_drafting_note(self, text: str) -> bool:
        """Return ``True`` when ``text`` matches the drafting-note heuristics."""

        normalized = text.strip()
        if not normalized:
            return False
        normalized = normalized.replace("\u2014", "-").replace("\u2013", "-")
        stripped = normalized.lstrip(DRAFTING_NOTE_LEADING_WRAPPERS)
        if DRAFTING_NOTE_PATTERN.match(stripped):
            return True
        if DRAFTING_NOTE_NEAR_PATTERN.search(stripped[:40]):
            return True
        return False

    def assign_role(self, block: dict[str, Any], text: str) -> None:
        """Assign a drafting-note role to ``block`` when the text warrants it."""

        if block.get("role") is not None:
            return
        if block.get("type") == "heading":
            return
        if isinstance(block.get("list"), dict):
            return
        if self.looks_like_drafting_note(text):
            block["role"] = "drafting_note"
