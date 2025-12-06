
"""Analysis pipeline orchestrating `.docx` trackers."""

from __future__ import annotations

import itertools
from collections import defaultdict
from typing import Any, TypeAlias
from uuid import uuid4

from docx.table import Table
from docx.text.paragraph import Paragraph

from effilocal.doc.amended_paragraph import AmendedParagraph
from effilocal.doc.numbering import NumberingDefinitions
from effilocal.doc.numbering_inspector import NumberingInspector
from effilocal.doc.numbering_context import NumberingEvent
from effilocal.doc.paragraphs import build_paragraph_block
from effilocal.doc.tables import build_table_rows
from effilocal.doc.trackers import (
    AttachmentTracker,
    DefinitionTracker,
    DraftingNoteHelper,
    NumberingTracker,
    TocFieldTracker,
)
from effilocal.doc.trackers.base import TrackerEventConsumer
from effilocal.doc.trackers.protocols import (
    AttachmentTrackerProtocol,
    DefinitionTrackerProtocol,
    DraftingNoteHelperProtocol,
    NumberingTrackerProtocol,
    TocFieldTrackerProtocol,
)
from effilocal.util.hash import norm_text_hash

Block: TypeAlias = dict[str, Any]
BlockList: TypeAlias = list[Block]


class _ContentHashTracker:
    """Assign deterministic content hashes while avoiding collisions."""

    def __init__(self) -> None:
        self._counts: dict[str, int] = defaultdict(int)

    def next_hash(self, text: str) -> str:
        base = norm_text_hash(text)
        count = self._counts[base]
        self._counts[base] += 1
        if count == 0:
            return base
        return f"{base}#{count}"


class AnalysisPipeline:
    """Coordinate block construction and tracker enrichment for `.docx` parsing."""

    def __init__(
        self,
        *,
        numbering_defs: NumberingDefinitions | None = None,
        numbering_inspector: NumberingInspector | None = None,
        fallback_heading_label: str | None = None,
        attachment_tracker: AttachmentTrackerProtocol | None = None,
        definition_tracker: DefinitionTrackerProtocol | None = None,
        numbering_tracker: NumberingTrackerProtocol | None = None,
        toc_tracker: TocFieldTrackerProtocol | None = None,
        drafting_helper: DraftingNoteHelperProtocol | None = None,
        initial_section_id: str | None = None,
        use_value_objects: bool = False,
    ) -> None:
        self._hash_tracker = _ContentHashTracker()
        self._fallback_heading_label = fallback_heading_label
        self._attachment_tracker = attachment_tracker or AttachmentTracker()
        self._definition_tracker = definition_tracker or DefinitionTracker()
        self._numbering_tracker = numbering_tracker or NumberingTracker(
            numbering_defs or NumberingDefinitions(abstract_levels={}, instances={}),
            numbering_inspector,
        )
        self._toc_tracker = toc_tracker or TocFieldTracker()
        self._drafting_helper = drafting_helper or DraftingNoteHelper()
        self._current_section_id = initial_section_id or str(uuid4())
        self._table_counter = itertools.count(1)
        self._use_value_objects = use_value_objects
        self._list_contexts: dict[tuple[int, int], dict[str, Any]] = {}
        self._para_counter = 0
        # Trackers implementing TrackerEventConsumer receive numbering events. This list
        # is fixed at construction time because trackers are rarely swapped dynamically.
        self._tracker_event_consumers: list[TrackerEventConsumer] = [
            tracker
            for tracker in (
                self._attachment_tracker,
                self._definition_tracker,
                self._toc_tracker,
            )
            if isinstance(tracker, TrackerEventConsumer)
        ]

    @property
    def current_section_id(self) -> str:
        """Return the section id currently in scope."""

        return self._current_section_id

    def process_paragraph(self, paragraph: Paragraph) -> Block | None:
        """Build and enrich a paragraph block, returning ``None`` for blanks.
        
        Uses AmendedParagraph to correctly handle track changes:
        - amended_text includes insertions (w:ins > w:t) but excludes deletions (w:delText)
        - amended_runs provides text content with deleted_text for deletions
        """
        # Create AmendedParagraph wrapper for track changes support
        amended = AmendedParagraph(paragraph)

        build_result, next_section_id = build_paragraph_block(
            paragraph,
            self._current_section_id,
            hash_provider=self._hash_tracker.next_hash,
            as_dataclass=self._use_value_objects,
            amended=amended,
        )
        if build_result is None:
            if self._definition_tracker is not None:
                self._definition_tracker.handle_blank()
            return None

        block_dict = (
            build_result.to_dict() if hasattr(build_result, "to_dict") else build_result
        )
        block: Block = block_dict  # type: ignore[assignment]
        
        # Add runs with formatting and revision info (text-based model)
        runs = amended.amended_runs
        if not runs and block.get('text'):
            # Create default run covering full text if no runs extracted
            runs = [{'text': block['text'], 'formats': []}]
        block['runs'] = runs
        
        block["para_idx"] = self._para_counter
        self._para_counter += 1
        original_heading_section = block["section_id"] if block["type"] == "heading" else None
        self._current_section_id = next_section_id

        list_payload, group_id = self._apply_numbering_metadata(block)
        toc_result = self._synthesize_toc(paragraph)

        if list_payload is not None:
            self._apply_numbering_payload(block, list_payload, group_id)
        elif toc_result is not None:
            self._apply_toc_placeholder_list(block, toc_result)

        attachment_changed = self._apply_attachment_metadata(block)
        if attachment_changed:
            self._reset_numbering_state()

        block.pop("_docx_has_numbering", None)

        text_value = block["text"]
        self._merge_toc_metadata(block, toc_result, original_heading_section, text_value)

        heading_meta = block.get("heading")
        if heading_meta is None and self._fallback_heading_label:
            heading_meta = {
                "text": self._fallback_heading_label,
                "source": "none",
                "fallback_label": self._fallback_heading_label,
            }
            block["heading"] = heading_meta

        if self._definition_tracker is not None:
            if block["type"] == "heading":
                level_value = block.get("level")
                heading_level = int(level_value) if isinstance(level_value, int) else None
                self._definition_tracker.observe_heading(block.get("text", ""), heading_level)
            elif block["type"] == "paragraph":
                self._definition_tracker.annotate_paragraph(block, text_value)

        if isinstance(block.get("list"), dict):
            self._maybe_continue_list_sequence(block)
            self._store_list_context(block)
        elif block.get("type") == "heading":
            self._mark_heading_break()

        self._assign_role(block, text_value)
        return block

    def _apply_numbering_metadata(self, block: Block) -> tuple[dict[str, Any] | None, str | None]:
        if self._numbering_tracker is None:
            return None, None
        if self._numbering_tracker.paragraph_has_numbering(block):
            block["_docx_has_numbering"] = True
        return self._numbering_tracker.next_for_paragraph(block)

    def _synthesize_toc(self, paragraph: Paragraph) -> Any | None:
        if self._toc_tracker is None:
            return None
        return self._toc_tracker.synthesize(paragraph)

    def _apply_numbering_payload(
        self,
        block: Block,
        payload: dict[str, Any],
        group_id: str | None,
    ) -> None:
        block["list"] = payload
        block["restart_group_id"] = group_id
        if block["type"] == "paragraph":
            block["type"] = "list_item"
        format_value = str(block["list"].get("format") or "").lower()
        if format_value == "none":
            block["list"]["ordinal"] = ""
        self._dispatch_numbering_event(block, payload, group_id)

    def _apply_toc_placeholder_list(self, block: Block, toc_result: Any) -> None:
        block["list"] = toc_result.list_payload
        block["restart_group_id"] = toc_result.group_id

    def _apply_attachment_metadata(self, block: Block) -> bool:
        if self._attachment_tracker is None:
            block["attachment_id"] = None
            return False
        self._current_section_id, changed = self._attachment_tracker.apply(
            block,
            self._current_section_id,
        )
        return changed

    def _reset_numbering_state(self) -> None:
        if self._numbering_tracker is not None:
            self._numbering_tracker.reset_for_attachment()
        self._list_contexts.clear()

    def _merge_toc_metadata(
        self,
        block: Block,
        toc_result: Any | None,
        original_heading_section: str | None,
        text_value: str,
    ) -> None:
        if toc_result is None:
            return

        heading_meta = block.get("heading")
        if heading_meta is None:
            heading_meta = {"text": text_value, "source": "toc_synthesized"}
            block["heading"] = heading_meta

        has_list_payload = isinstance(block.get("list"), dict)
        if not has_list_payload:
            block["restart_group_id"] = toc_result.group_id
            if block["type"] != "heading":
                block["type"] = "heading"
                block["level"] = toc_result.level + 1
                new_section_id = str(uuid4())
                block["section_id"] = new_section_id
                self._current_section_id = new_section_id
            elif original_heading_section is not None:
                self._current_section_id = original_heading_section
            if block["list"] is None:
                block["list"] = toc_result.list_payload
            return

        block["restart_group_id"] = toc_result.group_id
        current_list = block["list"]
        fallback_list = toc_result.list_payload
        if block["type"] != "heading":
            block["type"] = "heading"
            block["level"] = toc_result.level + 1
            new_section_id = str(uuid4())
            block["section_id"] = new_section_id
            self._current_section_id = new_section_id
        else:
            block["level"] = toc_result.level + 1
            if original_heading_section is not None:
                self._current_section_id = original_heading_section

        if isinstance(current_list, dict) and isinstance(fallback_list, dict):
            # When real numbering exists, trust the calculated counters/ordinal from NumberingInspector
            # The TC field values are cached/hard-coded and may be outdated
            # Only copy metadata fields, not the actual counter values
            if fallback_list.get("format") and not current_list.get("format"):
                current_list["format"] = fallback_list["format"]
            if fallback_list.get("pattern") and not current_list.get("pattern"):
                current_list["pattern"] = fallback_list["pattern"]
            if "is_legal" in fallback_list and "is_legal" not in current_list:
                current_list["is_legal"] = fallback_list["is_legal"]
            if "restart_boundary" in fallback_list and "restart_boundary" not in current_list:
                current_list["restart_boundary"] = fallback_list["restart_boundary"]
            if "numbering_digest" in fallback_list:
                current_list.setdefault("numbering_digest", fallback_list["numbering_digest"])
            if "ordinal_at_parse" in fallback_list:
                current_list.setdefault("ordinal_at_parse", fallback_list["ordinal_at_parse"])

    def process_table(self, table: Table) -> BlockList:
        """Build and enrich blocks for the supplied table."""

        table_id = f"tbl_{next(self._table_counter)}"
        rows: list[list[Block]] = build_table_rows(
            table,
            table_id=table_id,
            section_id=self._current_section_id,
            hash_provider=self._hash_tracker.next_hash,
            fallback_heading_label=self._fallback_heading_label,
            as_dataclass=self._use_value_objects,
        )
        flattened: BlockList = []
        for row in rows:
            materialised_row: list[Block] = []
            for cell in row:
                if hasattr(cell, "to_dict"):
                    cell = cell.to_dict()  # type: ignore[assignment]
                materialised_row.append(cell)
            if self._definition_tracker is not None:
                self._definition_tracker.annotate_table_row(materialised_row)
            for block in materialised_row:
                if self._attachment_tracker is not None:
                    self._attachment_tracker.apply_to_table_block(block)
                else:
                    block["attachment_id"] = None
                self._assign_role(block, block.get("text", ""))
                flattened.append(block)
        return flattened

    def process_blank(self) -> None:
        """Notify trackers of a blank paragraph."""

        if self._definition_tracker is not None:
            self._definition_tracker.handle_blank()

    def _assign_role(self, block: Block, text: str) -> None:
        if self._drafting_helper is not None:
            self._drafting_helper.assign_role(block, text)

    def _maybe_continue_list_sequence(self, block: Block) -> None:
        list_payload = block.get("list")
        if not isinstance(list_payload, dict):
            return

        num_id = list_payload.get("num_id")
        level = list_payload.get("level")
        if not isinstance(num_id, int) or not isinstance(level, int):
            return

        key = (num_id, level)
        context = self._list_contexts.get(key)
        if not context or context.get("has_break"):
            return

        counters = list_payload.get("counters")
        prev_counters = context.get("counters")
        if not (isinstance(counters, list) and isinstance(prev_counters, list)):
            return
        if len(counters) != len(prev_counters):
            return
        if counters[:-1] != prev_counters[:-1]:
            return

        if counters[-1] != 1:
            return

        if list_payload.get("restart_boundary"):
            return

        if list_payload.get("format") != context.get("format"):
            return
        if list_payload.get("pattern") != context.get("pattern"):
            return

        new_counters = prev_counters[:-1] + [prev_counters[-1] + 1]
        list_payload["counters"] = new_counters
        list_payload["restart_boundary"] = False
        list_payload["list_instance_id"] = context.get("list_instance_id")
        list_payload["numbering_digest"] = context.get("numbering_digest")
        list_payload["ordinal_at_parse"] = context.get("ordinal_at_parse", 0) + 1
        block["restart_group_id"] = context.get("restart_group_id")
        list_payload["ordinal"] = self._format_ordinal(
            new_counters,
            list_payload.get("format"),
            list_payload.get("pattern"),
            list_payload.get("is_legal"),
        )

    def _store_list_context(self, block: Block) -> None:
        """Cache numbering state so later paragraphs can reuse counters after breaks."""
        list_payload = block.get("list")
        if not isinstance(list_payload, dict):
            return

        num_id = list_payload.get("num_id")
        level = list_payload.get("level")
        counters = list_payload.get("counters")
        if not isinstance(num_id, int) or not isinstance(level, int) or not isinstance(counters, list):
            return

        key = (num_id, level)
        self._list_contexts[key] = {
            "counters": counters[:],
            "format": list_payload.get("format"),
            "pattern": list_payload.get("pattern"),
            "restart_group_id": block.get("restart_group_id"),
            "list_instance_id": list_payload.get("list_instance_id"),
            "numbering_digest": list_payload.get("numbering_digest"),
            "ordinal_at_parse": list_payload.get("ordinal_at_parse") or 0,
            "has_break": False,
        }

        for other_key in [
            existing_key
            for existing_key in list(self._list_contexts.keys())
            if existing_key[0] == num_id and existing_key[1] > level
        ]:
            del self._list_contexts[other_key]

    def _mark_heading_break(self) -> None:
        for context in self._list_contexts.values():
            context["has_break"] = True

    def _dispatch_numbering_event(
        self,
        block: Block,
        payload: dict[str, Any],
        group_id: str | None,
    ) -> None:
        if not self._tracker_event_consumers:
            return
        # Use para_id for event matching since block["id"] is not yet assigned
        # para_id comes from Word's w14:paraId and is available at parse time
        para_id = block.get("para_id") or str(block.get("id"))
        event = NumberingEvent(
            block_id=para_id,
            payload=payload,
            restart_group_id=group_id,
        )
        for consumer in self._tracker_event_consumers:
            consumer.on_numbering_event(event)

    @staticmethod
    def _format_ordinal(
        counters: list[Any],
        num_fmt: Any,
        pattern: Any,
        is_legal: Any,
    ) -> str:
        if not counters:
            return ""

        pattern_str = str(pattern or "").strip()
        if pattern_str:
            rendered = pattern_str
            for idx, value in enumerate(counters, start=1):
                rendered = rendered.replace(f"%{idx}", str(value))
            if "%" in rendered:
                rendered = ".".join(str(value) for value in counters)
        else:
            if (isinstance(is_legal, bool) and is_legal) or len(counters) > 1:
                rendered = ".".join(str(value) for value in counters)
            else:
                rendered = str(counters[0])

        if isinstance(num_fmt, str) and num_fmt.lower() == "none":
            return ""

        return rendered
