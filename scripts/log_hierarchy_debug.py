"""Debug hierarchy inference and log internal state."""

from __future__ import annotations

import json
import sys
from collections import OrderedDict, defaultdict
from dataclasses import dataclass
from pathlib import Path
from textwrap import shorten
from typing import Any, Dict, Iterable, List, MutableMapping, Optional, Tuple


@dataclass(frozen=True)
class _ParentContext:
    block_id: str
    level: int
    group_id: Optional[str] = None
    counters: Optional[Tuple[int, ...]] = None


def _normalize_counters(raw: object) -> Tuple[int, ...]:
    if not isinstance(raw, list):
        return ()
    normalized: List[int] = []
    for value in raw:
        try:
            normalized.append(int(value))
        except (TypeError, ValueError):
            return ()
    return tuple(normalized)


def _are_sequential(previous: _ParentContext, succeeding: _ParentContext) -> bool:
    if not previous.counters or not succeeding.counters:
        return False
    if len(previous.counters) != len(succeeding.counters):
        return False
    if previous.counters[:-1] != succeeding.counters[:-1]:
        return False
    return succeeding.counters[-1] == previous.counters[-1] + 1


def load_blocks(path: Path) -> List[MutableMapping[str, Any]]:
    blocks: List[MutableMapping[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            blocks.append(json.loads(line))
    return blocks


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


INDENT_TOLERANCE = 240


def debug_infer(blocks: Iterable[MutableMapping[str, Any]]) -> None:
    block_list = list(blocks)
    if not block_list:
        print("No blocks supplied", file=sys.stderr)
        return

    by_id: Dict[str, MutableMapping[str, Any]] = {}
    position_by_id: Dict[str, int] = {}
    sibling_counter: Dict[Optional[str], int] = defaultdict(int)
    heading_stack: List[_ParentContext] = []
    list_stack: List[_ParentContext] = []
    clause_root_context: Optional[Dict[str, Any]] = None
    plain_runs: Dict[Optional[str], str] = {}
    counter_context: Dict[tuple, _ParentContext] = {}
    last_numbered_by_group: Dict[Optional[str], Dict[int, _ParentContext]] = defaultdict(dict)
    last_numbered_any_by_group: Dict[Optional[str], _ParentContext] = {}
    recent_ordinals_by_group: Dict[Optional[str], OrderedDict[Tuple[str, int], _ParentContext]] = defaultdict(OrderedDict)
    recent_ordinals_global: OrderedDict[Tuple[str, int], _ParentContext] = OrderedDict()

    for position, block in enumerate(block_list):
        block_id = str(block["id"])
        by_id[block_id] = block
        position_by_id[block_id] = position
        block.setdefault("child_block_ids", [])
        block.setdefault("parent_block_id", None)
        block.setdefault("sibling_ordinal", 0)
        block.setdefault("clause_group_id", None)
        block.setdefault("continuation_of", None)

    next_numbered_lookup: List[Dict[int, _ParentContext]] = [{} for _ in block_list]
    next_numbered_by_group: Dict[Optional[str], Dict[int, _ParentContext]] = {}
    for index in range(len(block_list) - 1, -1, -1):
        block = block_list[index]
        group_id = block.get("restart_group_id")
        current_map = next_numbered_by_group.get(group_id, {})
        next_numbered_lookup[index] = dict(current_map)
        list_payload = block.get("list")
        if not isinstance(list_payload, MutableMapping):
            continue
        fmt = str(list_payload.get("format") or "").lower()
        try:
            level = int(list_payload.get("level", 0))
        except (TypeError, ValueError):
            level = 0
        counters_tuple = _normalize_counters(list_payload.get("counters"))
        if fmt != "none":
            context_entry = _ParentContext(
                block_id=str(block["id"]),
                level=level,
                group_id=group_id,
                counters=counters_tuple,
            )
            per_group = next_numbered_by_group.setdefault(group_id, {})
            per_group[level] = context_entry
            for stale_level in [existing for existing in list(per_group.keys()) if existing > level]:
                del per_group[stale_level]

    def _register_parent(child: MutableMapping[str, Any], parent_id: Optional[str]) -> None:
        child["parent_block_id"] = parent_id
        sibling_key = parent_id
        ordinal = sibling_counter[sibling_key]
        child["sibling_ordinal"] = ordinal
        sibling_counter[sibling_key] += 1
        if parent_id is not None:
            parent = by_id.get(parent_id)
            if parent is not None:
                parent.setdefault("child_block_ids", []).append(child["id"])

    def _ordinal_for_ctx(ctx: Optional[_ParentContext]) -> str:
        if not ctx:
            return ""
        ctx_block = by_id.get(ctx.block_id) or {}
        payload = ctx_block.get("list") if isinstance(ctx_block.get("list"), MutableMapping) else None
        if payload is None:
            return ""
        ordinal_value = payload.get("ordinal")
        return str(ordinal_value) if ordinal_value is not None else ""

    def _format_for_ctx(ctx: Optional[_ParentContext]) -> str:
        if not ctx:
            return ""
        ctx_block = by_id.get(ctx.block_id) or {}
        payload = ctx_block.get("list") if isinstance(ctx_block.get("list"), MutableMapping) else None
        if payload is None:
            return ""
        return str(payload.get("format") or "").lower()

    def _has_alphanumeric(text: str) -> bool:
        return any(ch.isalnum() for ch in text)

    def describe(block_id: str) -> str:
        block = by_id[block_id]
        text = block.get("text") or block.get("heading", {}).get("text") or ""
        snippet = shorten(text.replace("\n", " "), width=60, placeholder="…")
        payload = block.get("list") if isinstance(block.get("list"), MutableMapping) else {}
        ordinal = payload.get("ordinal") if payload else ""
        return f"{block_id} | {ordinal or block.get('type')} | {snippet}"

    for index, block in enumerate(block_list):
        block_id = str(block["id"])
        block_type = block.get("type")
        next_numbered_map = next_numbered_lookup[index]
        list_payload = block.get("list") if isinstance(block.get("list"), MutableMapping) else None

        print("\n=== BLOCK", describe(block_id))

        def _finalise(block_type: Optional[str], parent_id: Optional[str], inner_payload: Optional[MutableMapping[str, Any]]) -> None:
            nonlocal clause_root_context

            indent = _indent_value(block)
            attachment_id = block.get("attachment_id")

            if block_type == "heading":
                block["clause_group_id"] = block.get("clause_group_id") or block_id
                clause_root_context = None
                plain_runs.clear()
                return

            if isinstance(inner_payload, MutableMapping):
                try:
                    level_val = int(inner_payload.get("level", 0))
                except (TypeError, ValueError):
                    level_val = 0
                plain_runs.pop(parent_id, None)
                fmt_val = str(inner_payload.get("format") or "").lower()
                if fmt_val == "none":
                    parent_clause_id = None
                    if parent_id is not None:
                        parent_clause_id = by_id.get(parent_id, {}).get("clause_group_id") or parent_id
                    block["clause_group_id"] = parent_clause_id or block.get("clause_group_id") or block_id
                    return
                if level_val == 0:
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

        parent_id: Optional[str] = None

        if list_payload:
            try:
                level = int(list_payload.get("level", 0))
            except (TypeError, ValueError):
                level = 0
            group_id = block.get("restart_group_id")
            group_cache = last_numbered_by_group.setdefault(group_id, {})

            while list_stack and (
                list_stack[-1].group_id != group_id
                or list_stack[-1].level >= level
            ):
                popped = list_stack.pop()
                print(f"  pop list_stack -> {popped}")

            if list_stack and list_stack[-1].group_id == group_id:
                parent_id = list_stack[-1].block_id
                print(f"  parent from list_stack: {parent_id}")
            elif heading_stack:
                parent_id = heading_stack[-1].block_id
                print(f"  parent from heading_stack: {parent_id}")

            counters_raw = list_payload.get("counters")
            counters_tuple = _normalize_counters(counters_raw) if isinstance(counters_raw, list) else ()
            if len(counters_tuple) > 1:
                prefix = counters_tuple[:-1]
                context = counter_context.get(prefix)
                if context is not None and context.block_id != parent_id:
                    print(f"  parent override by counter prefix {prefix}: {context.block_id}")
                    parent_id = context.block_id

            fmt = str(list_payload.get("format") or "").lower()
            print(
                "  list context",
                {
                    "fmt": fmt,
                    "level": level,
                    "group_id": group_id,
                    "counters": counters_tuple,
                    "parent_before_none": parent_id,
                },
            )

            def _ordinal_for_ctx(ctx: Optional[_ParentContext]) -> str:
                if not ctx:
                    return ""
                ctx_block = by_id.get(ctx.block_id) or {}
                payload = ctx_block.get("list") if isinstance(ctx_block.get("list"), MutableMapping) else None
                if payload is None:
                    return ""
                ordinal_value = payload.get("ordinal")
                return str(ordinal_value) if ordinal_value is not None else ""

            def _pattern_for_ctx(ctx: Optional[_ParentContext]) -> str:
                if not ctx:
                    return ""
                ctx_block = by_id.get(ctx.block_id) or {}
                payload = ctx_block.get("list") if isinstance(ctx_block.get("list"), MutableMapping) else None
                if payload is None:
                    return ""
                pattern_value = payload.get("pattern")
                return str(pattern_value) if pattern_value is not None else ""

            if fmt == "none":
                prev_any = last_numbered_any_by_group.get(group_id)

                preceding_chain: List[_ParentContext] = []
                fallback_level0_candidate: Optional[_ParentContext] = None
                seen_preceding: set[Tuple[str, int]] = set()
                for source_map in (recent_ordinals_by_group.get(group_id), recent_ordinals_global):
                    if not source_map:
                        continue
                    for ctx in reversed(list(source_map.values())):
                        ordinal_text_ctx = _ordinal_for_ctx(ctx)
                        if not ordinal_text_ctx or not _has_alphanumeric(ordinal_text_ctx):
                            continue
                        fmt_ctx = _format_for_ctx(ctx)
                        key_ctx = (fmt_ctx, ctx.level)
                        if key_ctx in seen_preceding:
                            continue
                        if ctx.level == 0 and fallback_level0_candidate is None:
                            fallback_level0_candidate = ctx
                        preceding_chain.append(ctx)
                        seen_preceding.add(key_ctx)

                succeeding_chain: List[_ParentContext] = []
                if index + 1 < len(block_list):
                    pattern_order: List[Tuple[str, int]] = []
                    succeeding_by_key: Dict[Tuple[str, int], _ParentContext] = {}
                    for forward_block in block_list[index + 1 :]:
                        list_forward = forward_block.get("list")
                        if not isinstance(list_forward, MutableMapping):
                            continue
                        fmt_forward = str(list_forward.get("format") or "").lower()
                        if not fmt_forward or fmt_forward == "none":
                            continue
                        pattern_forward = str(list_forward.get("pattern") or "")
                        if not pattern_forward or pattern_forward == "none":
                            continue
                        try:
                            level_forward = int(list_forward.get("level", 0))
                        except (TypeError, ValueError):
                            level_forward = 0
                        counters_forward = _normalize_counters(list_forward.get("counters"))
                        ctx = _ParentContext(
                            block_id=str(forward_block["id"]),
                            level=level_forward,
                            group_id=forward_block.get("restart_group_id"),
                            counters=counters_forward or None,
                        )
                        key = (pattern_forward, level_forward)
                        if key not in succeeding_by_key:
                            succeeding_by_key[key] = ctx
                            pattern_order.append(key)
                        ordinal_text_forward = str(list_forward.get("ordinal") or "")
                        if level_forward == 0 and ordinal_text_forward and _has_alphanumeric(ordinal_text_forward):
                            break

                    if pattern_order:
                        last_level0_key: Optional[Tuple[str, int]] = None
                        for key in pattern_order:
                            if succeeding_by_key[key].level == 0:
                                last_level0_key = key
                        if last_level0_key and pattern_order[-1] != last_level0_key:
                            pattern_order = [key for key in pattern_order if key != last_level0_key]
                            pattern_order.append(last_level0_key)
                        succeeding_chain = [succeeding_by_key[key] for key in pattern_order]

                def _ordinal_to_tuple(value: str) -> Optional[Tuple[int, ...]]:
                    if not value:
                        return None
                    parts: List[int] = []
                    cleaned = value.replace("(", "").replace(")", "").replace(" ", "")
                    for chunk in cleaned.split('.'):
                        if not chunk:
                            continue
                        try:
                            parts.append(int(chunk, 36))
                        except ValueError:
                            return None
                    return tuple(parts) if parts else None

                chosen_ctx: Optional[_ParentContext] = None
                matched_next: Optional[_ParentContext] = None
                fallback_level0_ctx: Optional[_ParentContext] = fallback_level0_candidate
                for candidate_ctx in preceding_chain:
                    ordinal_text = _ordinal_for_ctx(candidate_ctx)
                    if not ordinal_text or not _has_alphanumeric(ordinal_text):
                        continue
                    if candidate_ctx.level == 0 and fallback_level0_ctx is None:
                        fallback_level0_ctx = candidate_ctx
                    candidate_tuple = _ordinal_to_tuple(ordinal_text)
                    if candidate_tuple is None:
                        continue
                    expected_next = candidate_tuple[:-1] + (candidate_tuple[-1] + 1,)
                    match = None
                    for successor in succeeding_chain:
                        successor_text = _ordinal_for_ctx(successor)
                        successor_tuple = _ordinal_to_tuple(successor_text)
                        if successor_tuple is None:
                            continue
                        if (
                            successor.level == candidate_ctx.level
                            and successor_tuple == expected_next
                            and _format_for_ctx(successor) == _format_for_ctx(candidate_ctx)
                        ):
                            match = successor
                            break
                    if match is not None:
                        chosen_ctx = candidate_ctx
                        matched_next = match
                        break

                decision = "fallback_prev_any" if prev_any else "fallback_none"
                if chosen_ctx is not None:
                    parent_id = chosen_ctx.block_id
                    decision = f"lookahead_match_level_{chosen_ctx.level}"
                elif prev_any is not None and fallback_level0_ctx is not None:
                    parent_id = fallback_level0_ctx.block_id
                    decision = "fallback_level0"
                elif prev_any is not None:
                    parent_id = prev_any.block_id

                print(
                    "    fmt==none decision",
                    {
                        "prev_any": prev_any,
                        "preceding_chain": [
                            {
                                "block_id": ctx.block_id,
                                "level": ctx.level,
                                "ordinal": _ordinal_for_ctx(ctx),
                            }
                            for ctx in preceding_chain
                        ],
                        "matched_next": {
                            "block_id": matched_next.block_id,
                            "level": matched_next.level,
                            "ordinal": _ordinal_for_ctx(matched_next),
                        }
                        if matched_next
                        else None,
                        "fallback_level0": {
                            "block_id": fallback_level0_ctx.block_id,
                            "level": fallback_level0_ctx.level,
                            "ordinal": _ordinal_for_ctx(fallback_level0_ctx),
                        }
                        if fallback_level0_ctx
                        else None,
                        "succeeding_chain": [
                            {
                                "block_id": ctx.block_id,
                                "level": ctx.level,
                                "ordinal": _ordinal_for_ctx(ctx),
                            }
                            for ctx in succeeding_chain
                        ],
                        "chosen_decision": decision,
                        "parent_final": parent_id,
                    },
                )

                preceding_ordinals = [
                    {
                        "block_id": ctx.block_id,
                        "level": ctx.level,
                        "ordinal": _ordinal_for_ctx(ctx) or None,
                    }
                    for ctx in preceding_chain
                ]
                succeeding_ordinals = [
                    {
                        "block_id": ctx.block_id,
                        "level": ctx.level,
                        "ordinal": _ordinal_for_ctx(ctx) or None,
                    }
                    for ctx in succeeding_chain
                ]
                print(
                    "    numbering_window",
                    {
                        "preceding_ordinals": preceding_ordinals,
                        "succeeding_ordinals": succeeding_ordinals,
                    },
                )

            _register_parent(block, parent_id)
            _finalise(block_type, parent_id, list_payload)
            list_stack.append(
                _ParentContext(block_id=block_id, level=level, group_id=group_id)
            )
            print(f"  push list_stack -> {_ParentContext(block_id=block_id, level=level, group_id=group_id)}")

            if isinstance(counters_raw, list):
                context_entry = _ParentContext(
                    block_id=block_id,
                    level=level,
                    group_id=group_id,
                    counters=counters_tuple or None,
                )
                if counters_tuple:
                    if fmt == "none" and counters_tuple in counter_context:
                        pass
                    else:
                        counter_context[counters_tuple] = context_entry
                if fmt != "none":
                    group_cache[level] = context_entry
                    for stale_level in [
                        existing_level
                        for existing_level in list(group_cache.keys())
                        if existing_level > level
                    ]:
                        del group_cache[stale_level]
                    last_numbered_any_by_group[group_id] = context_entry
                    ordinal_current = str(list_payload.get("ordinal") or "")
                    if ordinal_current and _has_alphanumeric(ordinal_current):
                        fmt_current = fmt
                        key_recent = (fmt_current, level)
                        group_recent_map = recent_ordinals_by_group[group_id]
                        if key_recent in group_recent_map:
                            del group_recent_map[key_recent]
                        group_recent_map[key_recent] = context_entry
                        if key_recent in recent_ordinals_global:
                            del recent_ordinals_global[key_recent]
                        recent_ordinals_global[key_recent] = context_entry
                    if counters_tuple:
                        for key in [
                            existing_key
                            for existing_key in list(counter_context.keys())
                            if len(existing_key) > len(counters_tuple)
                        ]:
                            del counter_context[key]
            continue

        if block_type == "heading" and block.get("level") is not None:
            level = int(block["level"])
            while heading_stack and heading_stack[-1].level >= level:
                popped = heading_stack.pop()
                print(f"  pop heading_stack -> {popped}")
            list_stack.clear()
            last_numbered_by_group.clear()
            last_numbered_any_by_group.clear()

            heading_parent_id = heading_stack[-1].block_id if heading_stack else None
            _register_parent(block, heading_parent_id)
            _finalise(block_type, heading_parent_id, None)
            heading_stack.append(_ParentContext(block_id=block_id, level=level))
            print(f"  push heading_stack -> {_ParentContext(block_id=block_id, level=level)}")
            continue

        if heading_stack:
            parent_id = heading_stack[-1].block_id
            print(f"  parent from heading_stack (non-list): {parent_id}")
        elif list_stack:
            parent_id = list_stack[-1].block_id
            print(f"  parent from list_stack (non-list): {parent_id}")
        else:
            parent_id = block.get("parent_block_id")
            print(f"  parent inherited: {parent_id}")

        _register_parent(block, parent_id)
        _finalise(block_type, parent_id, None)
        if block_type == "heading":
            counter_context.clear()
            last_numbered_by_group.clear()
            last_numbered_any_by_group.clear()

        print(f"  parent assigned -> {parent_id}")
        print(f"  sibling ordinal -> {block['sibling_ordinal']}")


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python log_hierarchy_debug.py <blocks.jsonl>")
        sys.exit(1)

    input_path = Path(sys.argv[1]).expanduser().resolve()
    if not input_path.exists():
        print(f"Cannot find file: {input_path}", file=sys.stderr)
        sys.exit(1)

    blocks = load_blocks(input_path)
    debug_infer(blocks)


if __name__ == "__main__":
    main()
