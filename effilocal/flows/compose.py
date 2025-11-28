"""Utilities for composing chat responses with disclosure controls."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Mapping, Sequence

__all__ = ["compose_summary", "compose_blocks_list"]


def compose_summary(
    section_meta: Sequence[Mapping[str, Any]],
    synthesized_points: Sequence[Mapping[str, Any]],
    narration: str | None = None,
) -> str:
    """Compose a concise summary that cites section identifiers.

    Args:
        section_meta: Metadata for each section in display order. Each mapping must
            include `section_id` (or `id`) and may include `title`.
        synthesized_points: Analysis produced by the LLM. Each mapping must provide
            `section_id` (or `id`), a `summary` string, and may include
            `include_text` (truthy when verbatim text should appear) plus
            `quote_text` containing that clause text.
        narration: Optional natural-language narration explaining the LLM's tool
            usage or next actions. When provided it is prepended to the output.

    Returns:
        A formatted string that preserves narration, cites section IDs, and only
        inlines clause text when explicitly requested by the inputs.

    Raises:
        ValueError: If required identifiers are missing or if the inputs are empty.
    """

    if not section_meta:
        raise ValueError("section_meta must contain at least one entry")

    if not synthesized_points:
        raise ValueError("synthesized_points must contain at least one entry")

    ordered_sections: list[tuple[str, str | None]] = [
        (_extract_section_id(meta), _safe_str(meta.get("title")))
        for meta in section_meta
    ]

    points_by_section: dict[str, list[Mapping[str, Any]]] = defaultdict(list)

    for point in synthesized_points:
        section_id = _extract_section_id(point)
        summary = _safe_str(point.get("summary"))
        if not summary:
            raise ValueError("Each synthesized point must include a non-empty summary")
        points_by_section[section_id].append(point)

    lines: list[str] = []
    if narration:
        narration_text = narration.strip()
        if narration_text:
            lines.append(f"Narration: {narration_text}")

    for section_id, title in ordered_sections:
        points = points_by_section.get(section_id)
        if not points:
            continue

        summary_fragments = [_safe_str(point.get("summary")) for point in points]
        summary_text = " ".join(fragment for fragment in summary_fragments if fragment)

        if not summary_text:
            continue

        title_prefix = f"{title}: " if title else ""
        lines.append(f"- [{section_id}] {title_prefix}{summary_text}")

        for point in points:
            if _should_include_quote(point):
                quote = _safe_str(point.get("quote_text"))
                if quote:
                    lines.append(f"  > {quote}")

    if not lines:
        raise ValueError("No output generated from provided inputs")

    return "\n".join(lines)


def compose_blocks_list(
    block_ids: Sequence[str],
    paraphrases: Sequence[str],
    full_text: Mapping[str, str] | Sequence[str] | None = None,
    narration: str | None = None,
) -> str:
    """Compose a block-by-block disclosure list.

    Args:
        block_ids: Identifiers for the blocks, in display order.
        paraphrases: Paraphrased analysis for each block; must align with block_ids.
        full_text: Optional mapping (or sequence aligned with block_ids) containing
            verbatim clause text for blocks that require direct quoting.
        narration: Optional narration explaining tool usage or intent.

    Returns:
        A formatted string referencing each block ID. Verbatim text is only included
        for blocks present in `full_text`.

    Raises:
        ValueError: If block_ids/paraphrases lengths mismatch or identifiers missing.
    """

    if len(block_ids) != len(paraphrases):
        raise ValueError("block_ids and paraphrases must be the same length")

    if not block_ids:
        raise ValueError("block_ids must contain at least one entry")

    full_text_lookup = _normalise_full_text(full_text, block_ids)

    lines: list[str] = []
    if narration:
        narration_text = narration.strip()
        if narration_text:
            lines.append(f"Narration: {narration_text}")

    for block_id, paraphrase in zip(block_ids, paraphrases):
        clean_id = block_id.strip()
        clean_text = paraphrase.strip()
        if not clean_id:
            raise ValueError("Block identifiers must be non-empty strings")
        if not clean_text:
            raise ValueError("Paraphrases must be non-empty strings")

        lines.append(f"- [{clean_id}] {clean_text}")
        if clean_id in full_text_lookup:
            clause_text = full_text_lookup[clean_id].strip()
            if clause_text:
                lines.append(f"  > {clause_text}")

    return "\n".join(lines)


def _extract_section_id(payload: Mapping[str, Any]) -> str:
    section_id = payload.get("section_id") or payload.get("id")
    if not isinstance(section_id, str) or not section_id.strip():
        raise ValueError("Section identifiers must be provided as non-empty strings")
    return section_id.strip()


def _safe_str(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _should_include_quote(point: Mapping[str, Any]) -> bool:
    include_text = point.get("include_text")
    quote = point.get("quote_text")
    return bool(include_text and isinstance(quote, str) and quote.strip())


def _normalise_full_text(
    full_text: Mapping[str, str] | Sequence[str] | None,
    block_ids: Sequence[str],
) -> dict[str, str]:
    if full_text is None:
        return {}

    if isinstance(full_text, Mapping):
        return {
            block_id.strip(): text
            for block_id, text in full_text.items()
            if isinstance(block_id, str) and block_id.strip() and isinstance(text, str)
        }

    if len(full_text) != len(block_ids):
        raise ValueError(
            "When full_text is a sequence it must align with block_ids length"
        )

    lookup: dict[str, str] = {}
    for block_id, text in zip(block_ids, full_text):
        if isinstance(text, str) and text.strip():
            lookup[block_id.strip()] = text
    return lookup
