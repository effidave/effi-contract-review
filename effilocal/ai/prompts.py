"""Prompt builders for Sprint 2 labeling."""

from __future__ import annotations

from typing import Any, Mapping


LABELING_RULES: dict[str, str] = {
    "return": "json_only",
    "conservatism": "prefer_unsure_over_hallucination",
    "entities_note": "short names only",
    "no_full_text_request": "ask for specific sections later via tools",
}

SYSTEM_LABELING = (
    "You label legal document sections. "
    "Return JSON only, following the provided schema. "
    "Prefer 'unsure' over guessing."
)


def build_labeling_prompt(
    doc_id: str,
    inputs: Mapping[str, Any],
) -> tuple[str, dict[str, Any]]:
    """
    Build the system message and payload for the labeling LLM request.

    Args:
        doc_id: Identifier of the document under analysis.
        inputs: Precomputed data (outline, snippets, style summary, etc.).

    Returns:
        A tuple of (system_message, payload_dict).
    """

    outline = inputs.get("outline", [])
    snippets = inputs.get("snippets", {})
    style_summary = inputs.get("style_summary", {})

    payload: dict[str, Any] = {
        "doc_id": doc_id,
        "outline": outline,
        "snippets": snippets,
        "style_summary": style_summary,
        "rules": dict(LABELING_RULES),
    }

    return SYSTEM_LABELING, payload
