"""Relationships serialization helpers."""

from __future__ import annotations

from typing import Any, Iterable, Mapping, MutableMapping


def build_relationships(
    blocks: Iterable[MutableMapping[str, Any]],
) -> list[dict[str, Any]]:
    """Return relationship records for the supplied blocks."""

    relationships: list[dict[str, Any]] = []

    for block in blocks:
        block_id = str(block["id"])
        parent_block_id = block.get("parent_block_id")
        child_ids = [str(child) for child in block.get("child_block_ids", [])]
        sibling_ordinal = int(block.get("sibling_ordinal", 0))

        source = _infer_source(block)
        restart_group_id = block.get("restart_group_id")
        clause_group_id = block.get("clause_group_id")
        continuation_of = block.get("continuation_of")
        list_meta = _extract_list_meta(block.get("list"))

        relationships.append(
            {
                "block_id": block_id,
                "parent_block_id": str(parent_block_id) if parent_block_id else None,
                "child_block_ids": child_ids,
                "sibling_ordinal": sibling_ordinal,
                "source": source,
                "restart_group_id": str(restart_group_id) if restart_group_id else None,
                "list_meta": list_meta,
                "attachment_id": block.get("attachment_id"),
                "clause_group_id": str(clause_group_id) if clause_group_id else None,
                "continuation_of": str(continuation_of) if continuation_of else None,
            }
        )

    return relationships


def _infer_source(block: Mapping[str, Any]) -> str:
    block_type = block.get("type")
    if block_type == "heading":
        return "heading"
    if block_type == "list_item":
        return "list"
    if block.get("list") is not None:
        return "mixed"
    return "paragraph"


def _extract_list_meta(list_payload: Any) -> dict[str, Any] | None:
    if not isinstance(list_payload, Mapping):
        return None

    meta: dict[str, Any] = {}

    if "num_id" in list_payload:
        meta["num_id"] = list_payload.get("num_id")
    if "abstract_num_id" in list_payload:
        meta["abstract_num_id"] = list_payload.get("abstract_num_id")
    if "level" in list_payload:
        meta["level"] = list_payload.get("level")
    counters = list_payload.get("counters")
    if counters is not None:
        meta["counters"] = counters
    if "ordinal" in list_payload:
        meta["ordinal"] = list_payload.get("ordinal")
    if "format" in list_payload:
        meta["format"] = list_payload.get("format")
    if "pattern" in list_payload:
        meta["pattern"] = list_payload.get("pattern")
    if "is_legal" in list_payload:
        meta["is_legal"] = bool(list_payload.get("is_legal"))
    if "restart_boundary" in list_payload:
        meta["restart_boundary"] = bool(list_payload.get("restart_boundary"))
    if "list_instance_id" in list_payload:
        meta["list_instance_id"] = list_payload.get("list_instance_id")
    if "numbering_digest" in list_payload:
        meta["numbering_digest"] = list_payload.get("numbering_digest")
    if "ordinal_at_parse" in list_payload:
        meta["ordinal_at_parse"] = list_payload.get("ordinal_at_parse")

    return meta or None
