"""Utilities for constructing ``index.json`` summaries."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from copy import deepcopy
from typing import Any


def build_index(
    *,
    doc_id: str,
    source_filename: str,
    blocks: Sequence[Mapping[str, Any]],
    sections: Mapping[str, Any],
    filemap: Mapping[str, str],
    tag_ranges: Sequence[Mapping[str, Any]] | None = None,
    version: int = 1,
    doc_format: str = "docx",
    schema_version: str = "1.0.0",
) -> dict[str, Any]:
    """
    Build the ``index.json`` summary for a parsed document.

    Args:
        doc_id: Logical UUID for the document.
        source_filename: Original filename (for reference/debugging).
        blocks: Sequence of block dictionaries (see ``block.schema.json``).
        sections: Parsed sections tree (see ``sections.schema.json``).
        filemap: Mapping of artifact names to relative paths.
        tag_ranges: Optional list of logical tag range entries.
        version: Monotonic version for optimistic locking.
        doc_format: File format of the source document (currently ``docx``).
        schema_version: Version string describing the index schema.

    Returns:
        A dictionary ready to be written to ``index.json``.
    """

    block_count = len(blocks)
    char_count = sum(len(block.get("text", "")) for block in blocks)
    section_count = _count_sections(sections)
    ltu_count = block_count  # Each block represents a legal text unit in Sprint 1.
    max_section_depth = _derive_section_depth(sections)
    has_tag_ranges = bool(tag_ranges)

    filemap_copy = deepcopy(dict(filemap))
    if has_tag_ranges and "tag_ranges" not in filemap_copy:
        filemap_copy["tag_ranges"] = "tag_ranges.jsonl"

    return {
        "version": version,
        "doc_id": doc_id,
        "doc_format": doc_format,
        "source_filename": source_filename,
        "char_count": char_count,
        "block_count": block_count,
        "section_count": section_count,
        "ltu_count": ltu_count,
        "max_section_depth": max_section_depth,
        "has_tag_ranges": has_tag_ranges,
        "schema_version": schema_version,
        "filemap": filemap_copy,
    }


def _count_sections(sections: Mapping[str, Any]) -> int:
    root = sections.get("root", {})
    return sum(1 for _ in _iter_section_nodes(root))


def _derive_section_depth(sections: Mapping[str, Any]) -> int:
    if "depth_max" in sections:
        return int(sections["depth_max"])
    if "hierarchy_depth" in sections:
        return int(sections["hierarchy_depth"])
    root = sections.get("root", {})
    return _max_depth(root)


def _iter_section_nodes(node: Mapping[str, Any]) -> Iterable[Mapping[str, Any]]:
    for child in node.get("children", []):
        yield child
        yield from _iter_section_nodes(child)


def _max_depth(node: Mapping[str, Any], current: int = 0) -> int:
    children = node.get("children", [])
    if not children:
        return current
    return max(_max_depth(child, current + 1) for child in children)
