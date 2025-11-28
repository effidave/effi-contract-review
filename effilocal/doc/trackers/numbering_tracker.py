"""Numbering tracker used during `.docx` parsing."""

from __future__ import annotations

import hashlib
from typing import Any

from effilocal.doc.numbering import NumberingDefinitions
from effilocal.doc.numbering_inspector import NumberingInspector
from effilocal.doc.numbering_inspector.model import ParagraphData


class NumberingTracker:
    """Track numbering counters for paragraphs via the shared inspector."""

    def __init__(
        self,
        definitions: NumberingDefinitions,
        inspector: NumberingInspector | None = None,
    ) -> None:
        self._definitions = definitions
        self._inspector = inspector
        self._previous_counters: dict[int, list[int]] = {}
        self._group_seq: dict[int, int] = {}
        self._current_group: dict[int, str] = {}
        self._ordinal_counts: dict[str, int] = {}
        self._last_block_was_list: bool = False
        self._previous_list_num_id: int | None = None
        self._para_index = 0

    def reset_for_attachment(self) -> None:
        """Attachment transitions are driven by Word numbering semantics (no-op)."""
        return None

    def next_for_paragraph(
        self,
        paragraph: Paragraph,
    ) -> tuple[dict[str, Any], str | None] | tuple[None, None]:
        """Return numbering metadata for ``paragraph`` or ``(None, None)`` when not numbered."""

        if self._inspector is None:
            return None, None

        para_data = self._build_paragraph_data(paragraph)
        result = self._inspector.process_paragraph(para_data, debug=False)
        payload_and_group = self._build_list_payload(result.row)
        self._para_index += 1
        return payload_and_group

    def reset(self) -> None:
        """Completely clear tracker state."""

        self._previous_counters.clear()
        self._group_seq.clear()
        self._current_group.clear()
        self._ordinal_counts.clear()
        self._last_block_was_list = False
        self._previous_list_num_id = None
        self._para_index = 0
        if self._inspector is not None:
            self._inspector.reset()

    def paragraph_has_numbering(self, block: dict[str, Any]) -> bool:
        """Return True when the block carries numbering metadata."""

        direct = block.get("num_pr")
        if direct:
            return True
        style_id = block.get("style_id", "")
        if style_id and self._inspector is not None:
            return self._inspector.style_has_numbering(style_id)
        return False

    def _build_paragraph_data(self, block: dict[str, Any]) -> ParagraphData | None:
        para_id = block.get("para_id", "") or ""
        style_id = block.get("style_id", "") or ""
        text = block.get("text", "")
        num_pr = block.get("num_pr")
        if not isinstance(text, str):
            return None
        return ParagraphData(
            idx=self._para_index,
            para_id=para_id,
            style_id=style_id,
            text=text,
            direct_numpr=num_pr if isinstance(num_pr, dict) else None,
        )

    def _build_list_payload(
        self,
        row: dict[str, Any],
    ) -> tuple[dict[str, Any], str | None] | tuple[None, None]:
        num_id = row.get("numId")
        level = row.get("ilvl")
        counters = row.get("counters")
        if not isinstance(num_id, int) or not isinstance(level, int) or not isinstance(counters, list):
            self._last_block_was_list = False
            return None, None
        counters = self._trim_counters(counters)

        abstract_num_id = row.get("abstractNumId")
        chosen_def, override, base_def = self._definitions.get_level(num_id, level)
        fmt = row.get("format") or (
            (chosen_def.format if chosen_def else None)
            or (base_def.format if base_def else None)
        )
        pattern = row.get("pattern") or (
            (chosen_def.text if chosen_def else None)
            or (base_def.text if base_def else None)
        )
        is_legal = (
            chosen_def.is_legal
            if chosen_def is not None
            else base_def.is_legal if base_def is not None else False
        )
        start_override = override.start_override if override is not None else None
        previous_counters = self._previous_counters.get(num_id, [])
        top_counter = counters[0] if counters else None
        previous_top = previous_counters[0] if previous_counters else None

        is_new_group = False
        if counters:
            if level == 0:
                if not previous_counters:
                    is_new_group = True
                elif start_override is not None:
                    is_new_group = True
                elif previous_top is not None and top_counter is not None and top_counter <= previous_top:
                    is_new_group = True
            elif num_id not in self._current_group:
                is_new_group = True

        force_new_group = False
        if (
            self._last_block_was_list
            and self._previous_list_num_id is not None
            and self._previous_list_num_id != num_id
        ):
            force_new_group = True
        if force_new_group:
            is_new_group = True

        group_id = self._current_group.get(num_id)
        if is_new_group and counters:
            seq = self._group_seq.get(num_id, 0)
            group_id = self._make_group_id(num_id, seq)
            self._group_seq[num_id] = seq + 1
            self._current_group[num_id] = group_id
            self._ordinal_counts[group_id] = 0
        elif group_id is None and counters:
            seq = self._group_seq.get(num_id, 0)
            group_id = self._make_group_id(num_id, seq)
            self._group_seq[num_id] = seq + 1
            self._current_group[num_id] = group_id
            self._ordinal_counts[group_id] = 0

        ordinal_snapshot = 0
        if group_id is not None:
            ordinal_snapshot = self._ordinal_counts.get(group_id, 0) + 1
            self._ordinal_counts[group_id] = ordinal_snapshot

        self._last_block_was_list = True
        self._previous_list_num_id = num_id
        self._previous_counters[num_id] = counters

        payload = {
            "num_id": num_id,
            "abstract_num_id": abstract_num_id,
            "level": level,
            "counters": counters,
            "ordinal": row.get("rendered_number", ""),
            "format": fmt or "unknown",
            "pattern": pattern or "",
            "is_legal": is_legal,
            "restart_boundary": is_new_group,
            "list_instance_id": self._make_instance_id(num_id, abstract_num_id, group_id),
            "numbering_digest": self._make_numbering_digest(
                num_id=num_id,
                level=level,
                num_fmt=fmt or "unknown",
                pattern=pattern or "",
            ),
            "ordinal_at_parse": ordinal_snapshot,
        }
        return payload, group_id

    @staticmethod
    def _trim_counters(counters: list[int]) -> list[int]:
        trimmed = list(counters)
        while trimmed and trimmed[-1] == 0:
            trimmed.pop()
        return trimmed or counters

    @staticmethod
    def _make_group_id(num_id: int, seq: int) -> str:
        """Compute a stable group identifier for list restarts."""

        digest = hashlib.sha1(f"{num_id}:{seq}".encode("utf-8")).hexdigest()
        return f"listgrp-{digest}"

    @staticmethod
    def _make_instance_id(
        num_id: int,
        abstract_num_id: int | None,
        group_id: str | None,
    ) -> str:
        """Create a consistent identifier for a numbering instance."""

        components = [
            str(num_id),
            str(abstract_num_id) if abstract_num_id is not None else "",
            group_id or "",
        ]
        digest = hashlib.sha1("|".join(components).encode("utf-8")).hexdigest()
        return f"listinst-{digest}"

    @staticmethod
    def _make_numbering_digest(
        *,
        num_id: int,
        level: int,
        num_fmt: str | None,
        pattern: str | None,
    ) -> str:
        """Return a hash that captures numbering semantics for comparison."""

        components = [
            str(num_id),
            str(level),
            (num_fmt or "").strip().lower(),
            (pattern or "").strip(),
        ]
        digest = hashlib.sha1("|".join(components).encode("utf-8")).hexdigest()
        return f"num-{digest}"
