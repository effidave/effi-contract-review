"""Redaction utilities for masking sensitive content in snippets."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, List, Mapping, Pattern


@dataclass(frozen=True)
class RedactionRule:
    """Definition of a redaction rule."""

    pattern: Pattern[str]
    replacement: str


DEFAULT_RULES: List[RedactionRule] = [
    # Mask email addresses (simple heuristic, avoiding most punctuation pitfalls).
    RedactionRule(
        pattern=re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
        replacement="***EMAIL***",
    ),
    # Mask phone numbers with optional spaces, hyphens, or parentheses.
    RedactionRule(
        pattern=re.compile(r"\+?\d[\d\s().-]{6,}\d"),
        replacement="***PHONE***",
    ),
]


def redact_text(text: str, rules: Iterable[RedactionRule] | None = None) -> str:
    """Redact sensitive information from the provided text.

    Args:
        text: Input string to redact.
        rules: Optional iterable of `RedactionRule` instances to apply. Defaults
            to the module-level `DEFAULT_RULES`.

    Returns:
        The redacted string.
    """

    if not text:
        return text

    active_rules = list(DEFAULT_RULES if rules is None else rules)
    redacted = text
    for rule in active_rules:
        redacted = rule.pattern.sub(rule.replacement, redacted)
    return redacted


def redact_snippets(snippets: Mapping[str, str], rules: Iterable[RedactionRule] | None = None) -> dict[str, str]:
    """Return a copy of snippets with redaction applied to each value."""

    return {section_id: redact_text(content, rules) for section_id, content in snippets.items()}
