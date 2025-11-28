"""Dispatcher scaffolding for Sprint 3 document tools."""

from __future__ import annotations

import json
import re
import time
from collections import deque
from pathlib import Path
from typing import Any, Mapping, Sequence

from effilocal.flows.label_doc import build_outline
from effilocal.tools import audit, limits

FIXTURES_ROOT = Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "data"
DOC_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9-]{0,127}$")


def get_doc_outline(*, doc_id: str) -> Mapping[str, Any]:
    """Return the outline metadata for the requested document."""
    start_time = time.perf_counter()
    sections_path, blocks_path = _resolve_artifact_paths(doc_id)
    outline = build_outline(sections_path, blocks_path)
    result = {
        "doc_id": doc_id,
        "sections": [
            {
                "id": entry.get("section_id"),
                "title": entry.get("title"),
                "level": entry.get("level"),
                "block_count": entry.get("block_count"),
                "char_count": entry.get("char_count"),
            }
            for entry in outline
        ],
    }
    _log_tool_call(
        tool="get_doc_outline",
        doc_id=doc_id,
        args={"doc_id": doc_id},
        truncated=False,
        start_time=start_time,
    )
    return result


def get_content_by_range(
    *,
    doc_id: str,
    start_block: int,
    end_block: int,
    redact: bool | None = None,
) -> Mapping[str, Any]:
    """Return blocks within the inclusive range for the document."""

    start_time = time.perf_counter()
    if start_block < 0 or end_block < start_block:
        raise ValueError("Invalid block range")

    _, blocks_path = _resolve_artifact_paths(doc_id)
    blocks = _load_blocks(blocks_path)
    if end_block >= len(blocks):
        raise ValueError("Invalid block range")

    max_blocks = limits.MAX_BLOCKS
    max_chars = limits.MAX_CHARS
    if max_blocks <= 0 or max_chars <= 0:
        raise ValueError("Invalid dispatcher caps configuration")

    sliced = blocks[start_block : end_block + 1]
    selected: list[dict[str, Any]] = []
    char_total = 0
    truncated = False
    apply_redaction = bool(redact)

    for block in sliced:
        text = block.get("text", "") or ""
        next_char_total = char_total + len(text)
        if len(selected) >= max_blocks or next_char_total > max_chars:
            truncated = True
            break
        selected.append(block)
        char_total = next_char_total

    if not selected and sliced:
        # Always return at least one block to prevent infinite pagination loops.
        selected.append(sliced[0])
        truncated = True

    next_page: dict[str, Any] | None = None
    if truncated:
        next_start = start_block + len(selected)
        if next_start <= end_block:
            next_page = {
                "start_block": next_start,
                "end_block": end_block,
            }

    result = {
        "blocks": [
            {
                "id": block.get("id"),
                "text": _redact_text(block.get("text", "") or "", apply_redaction),
            }
            for block in selected
        ],
        "truncated": truncated,
        "next_page": next_page,
    }
    _log_tool_call(
        tool="get_content_by_range",
        doc_id=doc_id,
        args={
            "start_block": start_block,
            "end_block": end_block,
            "redact": bool(redact),
        },
        truncated=truncated,
        start_time=start_time,
    )
    return result


def get_section(
    *,
    doc_id: str,
    section_id: str,
    redact: bool | None = None,
) -> Mapping[str, Any]:
    """Return the blocks belonging to a document section."""

    start_time = time.perf_counter()
    sections_path, blocks_path = _resolve_artifact_paths(doc_id)
    section = _find_section_by_id(sections_path, section_id)
    if section is None:
        raise ValueError(f"Section not found: {section_id}")

    block_ids = section.get("block_ids", [])
    if not block_ids:
        return {
            "section_id": section_id,
            "blocks": [],
            "truncated": False,
            "next_page": None,
        }

    blocks = _load_blocks(blocks_path)
    blocks_by_id: dict[str, dict[str, Any]] = {
        str(block.get("id")): block
        for block in blocks
        if isinstance(block.get("id"), str)
    }
    ordered_blocks: list[dict[str, Any]] = []
    for candidate in block_ids:
        if not isinstance(candidate, str):
            continue
        block = blocks_by_id.get(candidate)
        if block is not None:
            ordered_blocks.append(block)

    max_blocks = limits.MAX_BLOCKS
    max_chars = limits.MAX_CHARS
    if max_blocks <= 0 or max_chars <= 0:
        raise ValueError("Invalid dispatcher caps configuration")

    selected: list[dict[str, Any]] = []
    char_total = 0
    truncated = False
    apply_redaction = bool(redact)

    for block in ordered_blocks:
        text = block.get("text", "") or ""
        next_char_total = char_total + len(text)
        if len(selected) >= max_blocks or next_char_total > max_chars:
            truncated = True
            break
        selected.append(block)
        char_total = next_char_total

    if not selected and ordered_blocks:
        selected.append(ordered_blocks[0])
        truncated = True

    next_page: dict[str, Any] | None = None
    if truncated:
        next_start = len(selected)
        if next_start < len(ordered_blocks):
            next_page = {
                "start_block": next_start,
                "end_block": len(ordered_blocks) - 1,
            }

    result = {
        "section_id": section_id,
        "blocks": [
            {
                "id": block.get("id"),
                "text": _redact_text(block.get("text", "") or "", apply_redaction),
            }
            for block in selected
        ],
        "truncated": truncated,
        "next_page": next_page,
    }
    _log_tool_call(
        tool="get_section",
        doc_id=doc_id,
        args={
            "section_id": section_id,
            "redact": bool(redact),
        },
        truncated=truncated,
        start_time=start_time,
    )
    return result


def get_related_units(
    *,
    doc_id: str,
    block_id: str,
    hops: int = 1,
    include_group: bool = False,
) -> Mapping[str, Any]:
    """Return block identifiers related to the requested block."""

    start_time = time.perf_counter()
    if hops < 1:
        raise ValueError("hops must be >= 1")

    relationships_path, blocks_path = _resolve_relationships_paths(doc_id)
    relationships_payload = _load_relationships(relationships_path)
    relationships = relationships_payload.get("relationships", [])
    block_map: dict[str, Mapping[str, Any]] = {
        entry.get("block_id"): entry for entry in relationships if entry.get("block_id")
    }

    if block_id not in block_map:
        raise ValueError(f"Unknown block_id: {block_id}")

    blocks = _load_blocks(blocks_path)
    ordering: dict[str, int] = {
        str(block.get("id")): index for index, block in enumerate(blocks)
    }

    sibling_ordinals = {
        entry["block_id"]: int(entry.get("sibling_ordinal", 0))
        for entry in relationships
        if entry.get("block_id")
    }

    related: list[str] = []
    seen: set[str] = {block_id}

    def _add_candidate(candidate: str | None) -> None:
        if candidate and candidate not in seen:
            related.append(candidate)
            seen.add(candidate)

    def _sorted_children(parent_id: str | None) -> list[str]:
        if not parent_id or parent_id not in block_map:
            return []
        child_ids = list(block_map[parent_id].get("child_block_ids", []))
        return sorted(child_ids, key=lambda cid: sibling_ordinals.get(cid, 0))

    anchor_rel = block_map[block_id]
    parent_id = anchor_rel.get("parent_block_id")
    _add_candidate(parent_id)

    if parent_id and parent_id in block_map:
        siblings = [
            sib_id
            for sib_id in _sorted_children(parent_id)
            if sib_id != block_id
        ]
        for sibling in siblings:
            _add_candidate(sibling)

    for child_id in _sorted_children(block_id):
        _add_candidate(child_id)

    if hops > 1:
        queue: deque[tuple[str, int]] = deque()
        queue.append((block_id, 0))
        visited: set[str] = {block_id}

        layered: dict[int, list[str]] = {}

        while queue:
            current_id, distance = queue.popleft()
            if distance >= hops:
                continue

            current_rel = block_map[current_id]
            neighbours: list[str] = []
            parent = current_rel.get("parent_block_id")
            if parent:
                neighbours.append(parent)
            neighbours.extend(current_rel.get("child_block_ids", []))

            for neighbour in neighbours:
                if neighbour in visited:
                    continue
                visited.add(neighbour)
                queue.append((neighbour, distance + 1))
                if distance + 1 > 1:
                    layered.setdefault(distance + 1, []).append(neighbour)

        for distance in sorted(layered):
            nodes = layered[distance]
            nodes.sort(key=lambda node_id: ordering.get(node_id, len(ordering)))
            for node_id in nodes:
                _add_candidate(node_id)

    if include_group:
        group_id = anchor_rel.get("restart_group_id")
        if group_id:
            grouped_ids = [
                entry_id
                for entry_id, entry in block_map.items()
                if entry.get("restart_group_id") == group_id
            ]
            grouped_ids.sort(key=lambda node_id: ordering.get(node_id, len(ordering)))
            for node_id in grouped_ids:
                _add_candidate(node_id)

    related_blocks = [
        _relationship_metadata(block_map[node_id])
        for node_id in related
        if node_id in block_map
    ]

    result = {
        "doc_id": doc_id,
        "block_id": block_id,
        "anchor_block": _relationship_metadata(anchor_rel),
        "related_block_ids": related,
        "related_blocks": related_blocks,
        "truncated": False,
        "next_page": None,
    }
    _log_tool_call(
        tool="get_related_units",
        doc_id=doc_id,
        args={
            "block_id": block_id,
            "hops": hops,
            "include_group": bool(include_group),
        },
        truncated=False,
        start_time=start_time,
    )
    return result


def get_by_tag(
    *,
    doc_id: str,
    label: str,
) -> Mapping[str, Any]:
    """Return tag ranges matching the supplied label."""

    start_time = time.perf_counter()
    if not isinstance(label, str) or not label.strip():
        raise ValueError("label must be a non-empty string")
    label = label.strip()

    tag_path, blocks_path = _resolve_tag_paths(doc_id)
    tag_ranges = _load_tag_ranges(tag_path)
    blocks = _load_blocks(blocks_path)

    block_order: list[str] = []
    ordering: dict[str, int] = {}
    for index, block in enumerate(blocks):
        block_id_value = str(block.get("id"))
        block_order.append(block_id_value)
        ordering[block_id_value] = index

    matches_with_index: list[tuple[int, dict[str, Any]]] = []
    seen_blocks: set[str] = set()
    ordered_blocks: list[str] = []

    for tag in tag_ranges:
        if str(tag.get("label")) != label:
            continue
        block_ids = _resolve_tag_block_ids(tag, block_order, ordering)
        if not block_ids:
            continue

        sorted_block_ids = sorted(
            block_ids,
            key=lambda bid: ordering.get(bid, len(ordering)),
        )
        start_index = ordering.get(sorted_block_ids[0], 0)
        end_index = ordering.get(sorted_block_ids[-1], start_index)

        payload: dict[str, Any] = {
            "tag_id": str(tag.get("id")),
            "block_ids": sorted_block_ids,
            "span": [start_index, end_index],
        }
        attributes = tag.get("attributes")
        if isinstance(attributes, Mapping) and attributes:
            payload["attributes"] = dict(attributes)

        matches_with_index.append((start_index, payload))

        for block_candidate in sorted_block_ids:
            if block_candidate not in seen_blocks:
                ordered_blocks.append(block_candidate)
                seen_blocks.add(block_candidate)

    matches_with_index.sort(key=lambda item: (item[0], item[1]["tag_id"]))
    matches: list[dict[str, Any]] = [payload for _, payload in matches_with_index]

    result = {
        "doc_id": doc_id,
        "label": label,
        "matches": matches,
        "blocks": ordered_blocks,
        "truncated": False,
        "next_page": None,
    }
    _log_tool_call(
        tool="get_by_tag",
        doc_id=doc_id,
        args={"label": label},
        truncated=False,
        start_time=start_time,
    )
    return result


def get_by_clause_number(
    *,
    doc_id: str,
    clause_number: str,
) -> Mapping[str, Any]:
    """Return block identifiers matching the supplied clause number."""

    start_time = time.perf_counter()
    clause_number = clause_number.strip()
    if not clause_number:
        raise ValueError("clause_number must be a non-empty string")

    _, blocks_path = _resolve_artifact_paths(doc_id)
    blocks = _load_blocks(blocks_path)
    ordering: dict[str, int] = {
        str(block.get("id")): index for index, block in enumerate(blocks)
    }
    block_lookup: dict[str, Mapping[str, Any]] = {
        str(block.get("id")): block for block in blocks if block.get("id")
    }
    clause_groups = _build_clause_group_index(blocks, ordering)

    normalized_query = _normalize_clause_label(clause_number)
    formatter_matches: list[dict[str, Any]] = []
    counter_matches: list[dict[str, Any]] = []
    parsed_tokens = _parse_clause_tokens(clause_number)

    for block in blocks:
        list_payload = block.get("list")
        if not isinstance(list_payload, Mapping):
            continue

        block_id = str(block.get("id"))
        ordinal = str(list_payload.get("ordinal") or "")
        normalized_ordinal = _normalize_clause_label(ordinal)
        if normalized_ordinal and normalized_ordinal == normalized_query:
            formatter_matches.append(block)
            continue

        if parsed_tokens is None:
            continue

        counters = list_payload.get("counters")
        if not isinstance(counters, list) or len(counters) != len(parsed_tokens):
            continue
        if _counters_match(counters, parsed_tokens):
            counter_matches.append(block)

    matches = formatter_matches or counter_matches
    matches.sort(key=lambda block: ordering.get(str(block.get("id")), len(ordering)))
    matched_ids = [str(block.get("id")) for block in matches]

    clauses: list[dict[str, Any]] = []
    seen_groups: set[str] = set()
    for block in matches:
        block_id = str(block.get("id"))
        group_id = _coerce_uuid(block.get("clause_group_id")) or block_id
        if group_id in seen_groups:
            continue
        seen_groups.add(group_id)

        member_ids = clause_groups.get(group_id, [block_id])
        continuation_block_ids = [
            member_id
            for member_id in member_ids
            if _coerce_uuid(block_lookup.get(member_id, {}).get("continuation_of")) == group_id
        ]

        clause_blocks: list[dict[str, Any]] = []
        for member_id in member_ids:
            block_entry = block_lookup.get(member_id)
            if block_entry:
                clause_blocks.append(_block_metadata(block_entry))
            else:
                clause_blocks.append(
                    {
                        "block_id": member_id,
                        "clause_group_id": None,
                        "continuation_of": None,
                        "attachment_id": None,
                    }
                )

        clauses.append(
            {
                "clause_group_id": group_id,
                "anchor_block_id": block_id,
                "block_ids": member_ids,
                "continuation_block_ids": continuation_block_ids,
                "blocks": clause_blocks,
            }
        )

    result = {
        "doc_id": doc_id,
        "clause_number": clause_number,
        "block_ids": matched_ids,
        "clauses": clauses,
        "truncated": False,
        "next_page": None,
    }
    _log_tool_call(
        tool="get_by_clause_number",
        doc_id=doc_id,
        args={"clause_number": clause_number},
        truncated=False,
        start_time=start_time,
    )
    return result


def _relationship_metadata(entry: Mapping[str, Any]) -> dict[str, Any]:
    """Return clause metadata for a relationship entry."""

    block_id_value = entry.get("block_id")
    block_id = str(block_id_value) if block_id_value else ""
    clause_group_id = _coerce_uuid(entry.get("clause_group_id")) or block_id or None

    return {
        "block_id": block_id,
        "clause_group_id": clause_group_id,
        "continuation_of": _coerce_uuid(entry.get("continuation_of")),
        "attachment_id": _coerce_uuid(entry.get("attachment_id")),
    }


def _block_metadata(block: Mapping[str, Any]) -> dict[str, Any]:
    """Return clause metadata for a block record."""

    block_id_value = block.get("id")
    block_id = str(block_id_value) if block_id_value else ""
    clause_group_id = _coerce_uuid(block.get("clause_group_id")) or block_id or None

    return {
        "block_id": block_id,
        "clause_group_id": clause_group_id,
        "continuation_of": _coerce_uuid(block.get("continuation_of")),
        "attachment_id": _coerce_uuid(block.get("attachment_id")),
    }


def _coerce_uuid(value: Any) -> str | None:
    """Return a string representation of a UUID-like value or None."""

    if value is None:
        return None
    value_str = str(value).strip()
    return value_str or None


def _build_clause_group_index(
    blocks: Sequence[Mapping[str, Any]],
    ordering: Mapping[str, int],
) -> dict[str, list[str]]:
    """Create a mapping of clause_group_id to ordered block identifiers."""

    groups: dict[str, list[str]] = {}
    for block in blocks:
        block_id_value = block.get("id")
        if not block_id_value:
            continue
        block_id = str(block_id_value)
        group_id = _coerce_uuid(block.get("clause_group_id")) or block_id
        groups.setdefault(group_id, []).append(block_id)

    for group_id, member_ids in groups.items():
        member_ids.sort(key=lambda bid: ordering.get(bid, len(ordering)))

    return groups


def _resolve_artifact_paths(doc_id: str) -> tuple[Path, Path]:
    doc_root = _validate_doc_root(doc_id)
    sections_path = doc_root / "sections.json"
    blocks_path = doc_root / "blocks.jsonl"
    if not sections_path.is_file() or not blocks_path.is_file():
        raise FileNotFoundError(f"Document artifacts missing for doc_id: {doc_id}")
    return sections_path, blocks_path


def _load_blocks(path: Path) -> list[dict[str, Any]]:
    data: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            data.append(json.loads(line))
    return data


def _load_relationships(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"Relationships artifact missing: {path}")
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, Mapping):
        raise ValueError("relationships.json must be an object")
    return dict(payload)


def _find_section_by_id(path: Path, section_id: str) -> dict[str, Any] | None:
    with path.open("r", encoding="utf-8") as handle:
        sections = json.load(handle)
    queue = sections.get("root", {}).get("children", [])
    while queue:
        node = queue.pop(0)
        if node.get("id") == section_id:
            return node
        queue.extend(node.get("children", []))
    return None


def _redact_text(text: str, should_redact: bool) -> str:
    if not should_redact:
        return text
    return limits.apply_redaction(text)


def _validate_doc_root(doc_id: str) -> Path:
    if not isinstance(doc_id, str) or not DOC_ID_PATTERN.fullmatch(doc_id):
        raise ValueError("Invalid doc_id")
    doc_root = FIXTURES_ROOT / doc_id
    if not doc_root.is_dir():
        raise FileNotFoundError(f"Document not found: {doc_id}")
    return doc_root


def _resolve_relationships_paths(doc_id: str) -> tuple[Path, Path]:
    doc_root = _validate_doc_root(doc_id)
    relationships_path = doc_root / "relationships.json"
    blocks_path = doc_root / "blocks.jsonl"
    if not relationships_path.is_file() or not blocks_path.is_file():
        raise FileNotFoundError(f"Document artifacts missing for doc_id: {doc_id}")
    return relationships_path, blocks_path


def _resolve_tag_paths(doc_id: str) -> tuple[Path, Path]:
    doc_root = _validate_doc_root(doc_id)
    tag_path = doc_root / "tag_ranges.jsonl"
    blocks_path = doc_root / "blocks.jsonl"
    if not tag_path.is_file() or not blocks_path.is_file():
        raise FileNotFoundError(f"Document artifacts missing for doc_id: {doc_id}")
    return tag_path, blocks_path


def _load_tag_ranges(path: Path) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped:
                continue
            entries.append(json.loads(stripped))
    return entries


def _resolve_tag_block_ids(
    tag: Mapping[str, Any],
    block_order: Sequence[str],
    ordering: Mapping[str, int],
) -> list[str]:
    attributes = tag.get("attributes")
    block_ids: list[str] = []

    if isinstance(attributes, Mapping):
        attr_block_id = attributes.get("block_id")
        if isinstance(attr_block_id, str):
            block_ids.append(attr_block_id)
        else:
            attr_block_ids = attributes.get("block_ids")
            if isinstance(attr_block_ids, Sequence):
                for candidate in attr_block_ids:
                    if isinstance(candidate, str):
                        block_ids.append(candidate)

    block_ids = [bid for bid in block_ids if bid in ordering]
    if block_ids:
        return block_ids

    anchors = tag.get("anchors")
    if not isinstance(anchors, Mapping):
        return []

    start_anchor = anchors.get("start")
    end_anchor = anchors.get("end")

    start_block_id = _extract_near_block_id(start_anchor)
    end_block_id = _extract_near_block_id(end_anchor) or start_block_id

    if not start_block_id or start_block_id not in ordering:
        return []
    if not end_block_id or end_block_id not in ordering:
        end_block_id = start_block_id

    start_index = ordering[start_block_id]
    end_index = ordering[end_block_id]
    if start_index > end_index:
        start_index, end_index = end_index, start_index

    return [block_order[index] for index in range(start_index, end_index + 1)]


def _extract_near_block_id(anchor: Any) -> str | None:
    if not isinstance(anchor, Mapping):
        return None
    candidate = anchor.get("near_block_id")
    return candidate if isinstance(candidate, str) else None


def _normalize_clause_label(value: str) -> str:
    return re.sub(r"[^0-9a-z]", "", value.lower())


def _counters_match(
    counters: Sequence[Any],
    target: Sequence[int],
) -> bool:
    try:
        normalized = [int(counter) for counter in counters]
    except (TypeError, ValueError):
        return False
    return normalized == list(target)


CLAUSE_TOKEN_RE = re.compile(r"[A-Za-z]+|[0-9]+")
ROMAN_CHARS = {"I", "V", "X", "L", "C", "D", "M"}


def _parse_clause_tokens(value: str) -> list[int] | None:
    tokens = CLAUSE_TOKEN_RE.findall(value)
    if not tokens:
        return None

    parsed: list[int] = []
    for token in tokens:
        if token.isdigit():
            parsed.append(int(token))
            continue

        token_upper = token.upper()
        if set(token_upper).issubset(ROMAN_CHARS):
            roman_value = _roman_to_int(token_upper)
            if roman_value is None:
                return None
            parsed.append(roman_value)
            continue

        letter_value = _letter_to_int(token)
        if letter_value is None:
            return None
        parsed.append(letter_value)

    return parsed


def _letter_to_int(token: str) -> int | None:
    value = 0
    for char in token:
        if not char.isalpha():
            return None
        value = value * 26 + (ord(char.lower()) - ord("a") + 1)
    return value


def _roman_to_int(token: str) -> int | None:
    roman_map = {
        "I": 1,
        "V": 5,
        "X": 10,
        "L": 50,
        "C": 100,
        "D": 500,
        "M": 1000,
    }
    total = 0
    prev_value = 0
    for char in reversed(token):
        value = roman_map.get(char)
        if value is None:
            return None
        if value < prev_value:
            total -= value
        else:
            total += value
            prev_value = value
    return total


def _log_tool_call(
    *,
    tool: str,
    doc_id: str,
    args: Mapping[str, Any],
    truncated: bool,
    start_time: float,
) -> None:
    duration_ms = (time.perf_counter() - start_time) * 1000
    audit.log_tool_call(
        tool=tool,
        doc_id=doc_id,
        args=args,
        truncated=truncated,
        duration_ms=duration_ms,
    )
