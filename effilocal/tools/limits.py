"""Default limits and redaction helper for Sprint 3 tools."""

from __future__ import annotations

from typing import Iterable

from effilocal.util.redact import RedactionRule, redact_text

MAX_BLOCKS = 50
MAX_CHARS = 8_000
DEFAULT_REDACT = "auto"


def apply_redaction(text: str, rules: Iterable[RedactionRule] | None = None) -> str:
    """Apply the shared redaction rules to a text snippet."""

    return redact_text(text, rules)
