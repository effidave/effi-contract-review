"""Definition section tracker and helpers."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any
from uuid import uuid4

from effilocal.doc.trackers.base import TrackerEventConsumer

DEFINITION_HEADING_PATTERN = re.compile(
    r"^(?:[0-9]+[.\s]+)?(?:definition[s]?|interpretation)\b",
    re.IGNORECASE,
)

DEFINITION_PHRASE_PATTERN = re.compile(
    r"""
    ^\s*(?:"|\u201c|\u2018)?
    (?P<term>[A-Z0-9][^"\u201c\u201d\u2018\u2019:\-\u2013\u2014"”]{0,80}?)
    (?:"|\u201d|\u2019)?\s+
    (?:
        shall\s+mean|
        means|
        has\s+the\s+meaning|
        refers\s+to
    )
    \s+(?P<body>.+)$
    """,
    re.IGNORECASE | re.VERBOSE,
)

DEFINITION_SEPARATOR_PATTERN = re.compile(
    r"""
    ^\s*(?:"|\u201c|\u2018)?
    (?P<term>[A-Z0-9][^"\u201c\u201d\u2018\u2019]{0,80}?)
    (?:"|\u201d|\u2019)?\s*
    (?:
        [:;\-\u2013\u2014"”]\s+(?P<body>.+) |
        \s+(?P<word_body>is\s+defined\s+as\s+.+)
    )
    $
    """,
    re.IGNORECASE | re.VERBOSE,
)

_TRAILING_QUOTES = "\"'\u2019\u201d"


@dataclass
class DefinitionMatch:
    term: str
    inline_definition: str | None = None


class DefinitionTracker(TrackerEventConsumer):
    """Track definition sections and tag term/body blocks."""

    def __init__(self) -> None:
        self._active: bool = False
        self._section_level: int | None = None
        self._current_definition_id: str | None = None

    def observe_heading(self, text: str, level: int | None) -> None:
        """Inspect a heading to determine whether definition tracking should start or stop."""
        if (
            level is not None
            and self._active
            and self._section_level is not None
            and level <= self._section_level
        ):
            self._deactivate()
        if text and level is not None and DEFINITION_HEADING_PATTERN.match(text.strip()):
            self._active = True
            self._section_level = level
            self._current_definition_id = None

    def handle_blank(self) -> None:
        """Clear the current definition context when encountering a blank line."""
        if self._active:
            self._current_definition_id = None

    def annotate_paragraph(self, block: dict[str, Any], text: str) -> None:
        """Annotate ``block`` with definition metadata when the paragraph signals a term or body."""
        if not self._active:
            return
        normalized = text.strip()
        if not normalized:
            self._current_definition_id = None
            return
        match = match_definition_term(normalized)
        if match is not None:
            definition_id = str(uuid4())
            metadata: dict[str, Any] = {
                "definition_id": definition_id,
                "term": match.term,
                "role": "term",
            }
            if match.inline_definition:
                metadata["inline_definition"] = match.inline_definition
            block["definition"] = metadata
            self._current_definition_id = definition_id
            return
        if self._current_definition_id is not None:
            block["definition"] = {
                "definition_id": self._current_definition_id,
                "role": "body",
            }

    def annotate_table_row(self, row_blocks: list[dict[str, Any]]) -> None:
        """Annotate a row of table cells that represents a definition term and body."""
        if not self._active:
            return
        non_empty = [block for block in row_blocks if block.get("text", "").strip()]
        if len(non_empty) < 2:
            return
        term_text = normalize_definition_term(non_empty[0]["text"])
        if not looks_like_definition_term(term_text):
            return
        definition_id = str(uuid4())
        non_empty[0]["definition"] = {
            "definition_id": definition_id,
            "term": term_text,
            "role": "term",
        }
        for block in non_empty[1:]:
            block["definition"] = {
                "definition_id": definition_id,
                "role": "body",
            }
        self._current_definition_id = None

    def is_active(self) -> bool:
        return self._active

    def reset(self) -> None:
        """Reset tracker state."""

        self._deactivate()

    def _deactivate(self) -> None:
        """Internal helper to disable tracking and clear state."""
        self._active = False
        self._section_level = None
        self._current_definition_id = None


def match_definition_term(text: str) -> DefinitionMatch | None:
    """Return a parsed term/body pair when ``text`` looks like a definition sentence."""
    match = DEFINITION_PHRASE_PATTERN.match(text)
    if match is None:
        match = DEFINITION_SEPARATOR_PATTERN.match(text)
        if match is None:
            return None
        body = match.group("body") or match.group("word_body")
    else:
        body = match.group("body")
    term = normalize_definition_term(match.group("term"))
    if not looks_like_definition_term(term):
        return None
    inline_definition = body.strip() if body else None
    if inline_definition:
        inline_definition = inline_definition.strip()
    return DefinitionMatch(term=term, inline_definition=inline_definition or None)


def normalize_definition_term(value: str) -> str:
    """Normalise a candidate definition term by trimming quotes and whitespace."""
    term = value.strip().strip(_TRAILING_QUOTES).strip()
    term = term.strip("\u201c\u2018\u201d\u2019\"'")
    return term


def looks_like_definition_term(term: str) -> bool:
    """Return ``True`` when ``term`` resembles a capitalised definition candidate."""
    cleaned = re.sub(r"[\"'\u2018\u2019\u201c\u201d()]", " ", term)
    cleaned = cleaned.replace("-", " ")
    words = [word for word in cleaned.split() if word]
    if not words:
        return False
    return all(word[0].isupper() for word in words if word)
