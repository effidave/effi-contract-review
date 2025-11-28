"""Section hierarchy builders."""

from __future__ import annotations

import re
from collections.abc import Iterable
from typing import Any, Dict, List, Tuple
from uuid import uuid4


_ROLE_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"^(background|recital[s]?|introduction|overview)\b"), "front_matter"),
    (re.compile(r"^(agreement|order)\s+detail[s]?\b"), "order_details"),
    (re.compile(r"^(effective|commencement|agreement)\s+date\b"), "agreement_date"),
    (re.compile(r"^(the\s+)?parties\b"), "parties"),
    (re.compile(r"^(signature[s]?|execution)\b"), "signatures"),
    (re.compile(r"^(definition[s]?|interpretation)\b"), "definitions"),
]


def assign_sections(blocks_iter: Iterable[dict[str, Any]], doc_id: str) -> dict[str, Any]:
    """
    Build a hierarchical section tree from a stream of document blocks.

    Numbered blocks take precedence when forming sections. Styled headings only create
    sections when numbering is absent. Plain paragraphs inherit the most recent section.
    """

    blocks = list(blocks_iter)
    root_children: List[dict[str, Any]] = []
    sections_by_id: Dict[str, dict[str, Any]] = {}
    section_depths: Dict[str, int] = {}
    number_stack: List[Tuple[int, dict[str, Any]]] = []
    heading_stack: List[Tuple[int, dict[str, Any]]] = []
    current_section: dict[str, Any] | None = None
    max_depth = 0
    main_body_assigned = False

    def _register_section(section: dict[str, Any], parent: dict[str, Any] | None) -> None:
        nonlocal max_depth

        if parent:
            parent["children"].append(section)
            parent["child_ids"].append(section["id"])
            section["parent_id"] = parent["id"]
            depth = section_depths[parent["id"]] + 1
        else:
            root_children.append(section)
            section["parent_id"] = None
            depth = 1
        section_depths[section["id"]] = depth
        max_depth = max(max_depth, depth)
        sections_by_id[section["id"]] = section

    def _assign_block(section: dict[str, Any], block: dict[str, Any]) -> None:
        block["section_id"] = section["id"]
        section["block_ids"].append(block["id"])
        section["char_count"] += len(block.get("text") or "")

    def _section_title(block: dict[str, Any], override: str | None = None) -> str:
        if override:
            return override
        heading_meta = block.get("heading") or {}
        return heading_meta.get("text") or block.get("text") or "Untitled section"

    def _new_section(
        block: dict[str, Any],
        *,
        level: int,
        parent: dict[str, Any] | None,
        role: str | None = None,
        title: str | None = None,
    ) -> dict[str, Any]:
        nonlocal main_body_assigned

        section_id = str(uuid4())
        attachment_id = block.get("attachment_id") or (parent.get("attachment_id") if parent else None)
        inferred_role = role if role is not None else _infer_section_role(block.get("text", ""), block.get("heading"))
        if inferred_role is None and parent is None and not attachment_id and not main_body_assigned:
            inferred_role = "main_body"
            main_body_assigned = True

        section = {
            "id": section_id,
            "ltu_id": f"ltu_{section_id}",
            "child_ids": [],
            "title": _section_title(block, title),
            "level": max(1, min(level, 6)),
            "block_ids": [],
            "char_count": 0,
            "children": [],
            "role": inferred_role,
            "attachment_id": attachment_id,
        }
        _register_section(section, parent)
        _assign_block(section, block)
        return section

    def _start_numbered_section(block: dict[str, Any], list_payload: dict[str, Any]) -> dict[str, Any]:
        nonlocal number_stack, heading_stack

        raw_level = list_payload.get("level")
        list_level = int(raw_level) if isinstance(raw_level, int) else 0
        while number_stack and number_stack[-1][0] >= list_level:
            number_stack.pop()
        parent = number_stack[-1][1] if number_stack else None
        section = _new_section(block, level=list_level + 1, parent=parent)
        number_stack.append((list_level, section))
        heading_stack = []
        return section

    def _start_heading_section(block: dict[str, Any]) -> dict[str, Any]:
        nonlocal heading_stack, number_stack

        raw_level = block.get("level")
        heading_level = int(raw_level) if isinstance(raw_level, int) else 1
        while heading_stack and heading_stack[-1][0] >= heading_level:
            heading_stack.pop()
        parent = heading_stack[-1][1] if heading_stack else None
        section = _new_section(block, level=heading_level, parent=parent)
        heading_stack.append((heading_level, section))
        number_stack = []
        return section

    for block in blocks:
        list_payload = block.get("list")
        if isinstance(list_payload, dict):
            current_section = _start_numbered_section(block, list_payload)
            continue

        if block.get("type") == "heading" and block.get("level"):
            current_section = _start_heading_section(block)
            continue

        if current_section is None:
            current_section = _new_section(
                block,
                level=1,
                parent=None,
                role="front_matter",
                title="Front Matter",
            )
            heading_stack = [(1, current_section)]
            number_stack = []
            continue

        _assign_block(current_section, block)

    section_count = len(sections_by_id)
    total_blocks = len(blocks)
    avg_blocks = (total_blocks / section_count) if section_count else 0.0

    return {
        "doc_id": doc_id,
        "hierarchy_depth": max_depth,
        "depth_max": max_depth,
        "avg_blocks_per_section": avg_blocks,
        "root": {"children": root_children},
    }


def _infer_section_role(text: str, heading_meta: dict[str, Any] | None) -> str | None:
    candidate = (heading_meta or {}).get("text") or text or ""
    norm = candidate.strip().lower()
    if not norm:
        return None

    norm = re.sub(r"[^\w\s]", " ", norm)
    norm = re.sub(r"\s+", " ", norm).strip()
    if not norm:
        return None

    for pattern, role in _ROLE_PATTERNS:
        if pattern.match(norm):
            return role
    return None
