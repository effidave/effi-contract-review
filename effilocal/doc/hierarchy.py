"""Infer block-level hierarchy relationships."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, MutableMapping, Optional


@dataclass(frozen=True)
class _ParentContext:
    """Track the active parent candidate for a block."""

    block_id: str
    level: int
    group_id: Optional[str] = None


INDENT_TOLERANCE = 240


def infer_block_hierarchy(blocks: Iterable[MutableMapping[str, Any]]) -> None:
    """Populate parent/child/sibling metadata on the supplied blocks."""

    block_list: List[MutableMapping[str, Any]] = list(blocks)
    if not block_list:
        return

    by_id: Dict[str, MutableMapping[str, Any]] = {}
    sibling_counter: Dict[Optional[str], int] = defaultdict(int)
    heading_stack: List[_ParentContext] = []
    list_stack: List[_ParentContext] = []
    clause_root_context: Optional[Dict[str, Any]] = None
    plain_runs: Dict[Optional[str], str] = {}
    counter_context: Dict[tuple, _ParentContext] = {}
    last_numbered: Optional[_ParentContext] = None

    def _indent_value(block: MutableMapping[str, Any]) -> int:
        indent_value = block.get("indent")

        def _coerce(value: object) -> int:
            if isinstance(value, bool):
                return int(value)
            if isinstance(value, (int, float)):
                return int(value)
            if isinstance(value, str):
                stripped = value.strip()
                if not stripped:
                    return 0
                try:
                    return int(stripped)
                except ValueError:
                    try:
                        return int(float(stripped))
                    except ValueError:
                        return 0
            return 0

        if isinstance(indent_value, dict):
            return _coerce(indent_value.get("left"))

        return _coerce(indent_value)

    for block in block_list:
        block_id = str(block["id"])
        by_id[block_id] = block
        block["child_block_ids"] = []
        block.setdefault("parent_block_id", None)
        block.setdefault("sibling_ordinal", 0)
        block.setdefault("clause_group_id", None)
        block.setdefault("continuation_of", None)

    def _register_parent(child: MutableMapping[str, Any], parent_id: Optional[str]) -> None:
        child["parent_block_id"] = parent_id
        sibling_key = parent_id
        ordinal = sibling_counter[sibling_key]
        child["sibling_ordinal"] = ordinal
        sibling_counter[sibling_key] += 1
        if parent_id is not None:
            parent = by_id.get(parent_id)
            if parent is not None:
                parent["child_block_ids"].append(child["id"])

    for block in block_list:
        block_id = str(block["id"])
        block_type = block.get("type")

        def _finalise(block_type: Optional[str], parent_id: Optional[str], list_payload: Optional[MutableMapping[str, Any]]) -> None:
            nonlocal clause_root_context

            indent = _indent_value(block)
            attachment_id = block.get("attachment_id")

            if block_type == "heading":
                block["clause_group_id"] = block.get("clause_group_id") or block_id
                clause_root_context = None
                plain_runs.clear()
                return

            if isinstance(list_payload, MutableMapping):
                try:
                    level = int(list_payload.get("level", 0))
                except (TypeError, ValueError):
                    level = 0
                plain_runs.pop(parent_id, None)
                fmt = str(list_payload.get("format") or "").lower()
                if fmt == "none":
                    parent_clause_id = None
                    if parent_id is not None:
                        parent_clause_id = by_id.get(parent_id, {}).get("clause_group_id") or parent_id
                    block["clause_group_id"] = parent_clause_id or block.get("clause_group_id") or block_id
                    return
                if level == 0:
                    root_id = block_id
                    if (
                        clause_root_context
                        and clause_root_context["parent_id"] == parent_id
                        and clause_root_context["attachment_id"] == attachment_id
                    ):
                        root_id = clause_root_context["root_id"]
                    block["clause_group_id"] = root_id
                    clause_root_context = {
                        "root_id": root_id,
                        "parent_id": parent_id,
                        "attachment_id": attachment_id,
                        "indent": indent,
                        "window": 2,
                    }
                else:
                    parent_clause_id = by_id.get(parent_id, {}).get("clause_group_id") if parent_id else None
                    block["clause_group_id"] = parent_clause_id or block.get("clause_group_id") or block_id
                return

            style_name = (block.get("style") or "").strip().lower()
            if style_name in {"list number", "list paragraph"}:
                plain_runs.pop(parent_id, None)
                block["clause_group_id"] = block_id
                clause_root_context = {
                    "root_id": block_id,
                    "parent_id": parent_id,
                    "attachment_id": attachment_id,
                    "indent": indent,
                    "window": 2,
                }
                return

            if style_name.startswith("list number ") and style_name not in {"list number", "list number "}:
                plain_runs.pop(parent_id, None)
                block["clause_group_id"] = block.get("clause_group_id") or block_id
                return

            assigned = False
            if clause_root_context:
                if (
                    clause_root_context["parent_id"] == parent_id
                    and clause_root_context["attachment_id"] == attachment_id
                    and clause_root_context["window"] > 0
                    and abs(indent - clause_root_context["indent"]) <= INDENT_TOLERANCE
                ):
                    block["continuation_of"] = clause_root_context["root_id"]
                    block["clause_group_id"] = clause_root_context["root_id"]
                    clause_root_context["window"] -= 1
                    if clause_root_context["window"] <= 0:
                        clause_root_context = None
                    assigned = True
                else:
                    clause_root_context = None

            if not assigned:
                group_id = plain_runs.get(parent_id)
                if group_id is None:
                    group_id = block_id
                    plain_runs[parent_id] = group_id
                block["clause_group_id"] = group_id

        list_payload = block.get("list")
        parent_id: Optional[str] = None
        if isinstance(list_payload, MutableMapping):
            try:
                level = int(list_payload.get("level", 0))
            except (TypeError, ValueError):
                level = 0
            group_id = block.get("restart_group_id")

            while list_stack and (
                list_stack[-1].group_id != group_id
                or list_stack[-1].level >= level
            ):
                list_stack.pop()

            if list_stack and list_stack[-1].group_id == group_id:
                parent_id = list_stack[-1].block_id
            elif heading_stack:
                parent_id = heading_stack[-1].block_id

            counters = list_payload.get("counters")
            if isinstance(counters, list) and len(counters) > 1:
                prefix = tuple(counters[:-1])
                context = counter_context.get(prefix)
                if context is not None and context.block_id != parent_id:
                    parent_id = context.block_id

            fmt = str(list_payload.get("format") or "").lower()
            nonlocal_last = last_numbered
            if fmt == "none" and parent_id is None and last_numbered is not None:
                parent_id = last_numbered.block_id

            _register_parent(block, parent_id)
            _finalise(block_type, parent_id, list_payload)
            list_stack.append(
                _ParentContext(block_id=block_id, level=level, group_id=group_id)
            )

            if isinstance(counters, list) and counters:
                context_entry = _ParentContext(
                    block_id=block_id, level=level, group_id=group_id
                )
                counter_context[tuple(counters)] = context_entry
                if fmt != "none":
                    last_numbered = context_entry

                for key in [
                    existing_key
                    for existing_key in list(counter_context.keys())
                    if len(existing_key) > len(counters)
                ]:
                    del counter_context[key]

            continue

        if block_type == "heading" and block.get("level") is not None:
            level = int(block["level"])
            while heading_stack and heading_stack[-1].level >= level:
                heading_stack.pop()
            list_stack.clear()
            last_numbered = None

            heading_parent_id = heading_stack[-1].block_id if heading_stack else None
            _register_parent(block, heading_parent_id)
            _finalise(block_type, heading_parent_id, None)
            heading_stack.append(_ParentContext(block_id=block_id, level=level))
            continue

        if heading_stack:
            parent_id = heading_stack[-1].block_id
        else:
            parent_id = block.get("parent_block_id")

        _register_parent(block, parent_id)
        _finalise(block_type, parent_id, None)
        if block_type == "heading":
            counter_context.clear()
