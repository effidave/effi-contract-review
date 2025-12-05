"""Attachment detection and metadata helpers."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Mapping
from uuid import uuid4

from effilocal.config.attachment_cues import (
    ATTACHMENT_KEYWORDS,
    ATTACHMENT_PATTERN_CUES,
    ATTACHMENT_PUNCTUATION,
)
from effilocal.doc.numbering_context import NumberingEvent
from effilocal.doc.trackers.base import TrackerEventConsumer


@dataclass
class AttachmentInfo:
    """Metadata describing an attachment anchor block."""

    attachment_id: str
    block_id: str
    type: str
    ordinal: str | None
    title: str | None
    parent_attachment_id: str | None
    level: int
    group_id: str | None = None
    from_heading: bool = False


class AttachmentTracker(TrackerEventConsumer):
    """Track attachment anchors and apply metadata to subsequent blocks."""

    _ROOT_TYPES = {"schedule", "attachment"}
    _PARENT_FALLBACKS = {
        "annex": {"schedule", "attachment", "appendix"},
        "appendix": {"schedule", "attachment", "annex"},
        "exhibit": {"schedule", "attachment", "annex", "appendix"},
    }

    def __init__(self) -> None:
        self._stack: list[AttachmentInfo] = []
        self._processed_groups: set[str] = set()
        self._pending_heading_text: str | None = None
        self._pending_numbering_events: dict[str, NumberingEvent] = {}

    @property
    def current_attachment_id(self) -> str | None:
        if not self._stack:
            return None
        return self._stack[-1].attachment_id

    def apply(
        self,
        block: dict[str, Any],
        current_section_id: str,
    ) -> tuple[str, bool]:
        """Apply attachment detection to a block and return the updated section id."""
        info = self._detect_anchor(block)
        if info is not None:
            current_section_id = self._apply_attachment(block, current_section_id, info)
            self._pending_heading_text = None
            return current_section_id, True

        # Look up by para_id since block["id"] is not yet assigned during iteration
        lookup_key = block.get("para_id") or block.get("id")
        numbering_event = self._pending_numbering_events.pop(lookup_key, None)
        numbered_info = self._detect_numbered_attachment(block, numbering_event)
        if numbered_info is not None:
            current_section_id = self._apply_attachment(block, current_section_id, numbered_info)
            self._pending_heading_text = None
            return current_section_id, True

        if block["type"] == "heading":
            level = block.get("level")
            if isinstance(level, int) and level <= 1:
                self._stack.clear()
        block["attachment_id"] = self.current_attachment_id
        if not isinstance(block.get("list"), Mapping):
            text_value = block.get("text")
            if isinstance(text_value, str) and text_value.strip():
                self._pending_heading_text = text_value
        else:
            self._pending_heading_text = None
        return current_section_id, False

    def apply_to_table_block(self, block: dict[str, Any]) -> None:
        """Propagate the current attachment id onto a table cell block."""

        block["attachment_id"] = self.current_attachment_id

    def reset(self) -> None:
        """Clear tracker state."""

        self._stack.clear()
        self._processed_groups.clear()
        self._pending_heading_text = None
        self._pending_numbering_events.clear()

    def on_numbering_event(self, event: NumberingEvent) -> None:
        """Store numbering metadata for later attachment evaluation."""

        self._pending_numbering_events[event.block_id] = event
        self._processed_groups.clear()

    def _register_anchor(self, block: dict[str, Any], info: AttachmentInfo) -> None:
        """Record a newly detected attachment anchor and adjust the stack."""
        new_type = info.type
        if new_type in self._ROOT_TYPES:
            self._stack.clear()
            info.parent_attachment_id = None
            info.level = max(info.level, 1)
        else:
            allowed = self._PARENT_FALLBACKS.get(new_type)
            parent = None
            if allowed:
                for candidate in reversed(self._stack):
                    if candidate.type in allowed:
                        parent = candidate
                        break
            if parent is None and allowed is None and self._stack:
                for candidate in reversed(self._stack):
                    if candidate.type != new_type:
                        parent = candidate
                        break
            if parent is not None and info.parent_attachment_id is None:
                info.parent_attachment_id = parent.attachment_id
                info.level = parent.level + 1
        self._stack = [entry for entry in self._stack if entry.level < info.level]
        self._stack.append(info)
        if info.group_id:
            self._processed_groups.add(info.group_id)

    def _apply_attachment(
        self,
        block: dict[str, Any],
        current_section_id: str,
        info: AttachmentInfo,
    ) -> str:
        self._register_anchor(block, info)
        if info.from_heading or block["type"] == "heading":
            if block["type"] != "heading":
                block["type"] = "heading"
            block["heading"] = block.get("heading") or {
                "text": block["text"],
                "source": "explicit",
            }
            block["heading"]["text"] = block["heading"].get("text") or block["text"]
            if block["heading"].get("source") == "none":
                block["heading"]["source"] = "explicit"
            block["level"] = info.level
            current_section_id = str(uuid4())
            block["section_id"] = current_section_id
        else:
            current_section_id = str(uuid4())
            block["section_id"] = current_section_id
        block["attachment"] = {
            "attachment_id": info.attachment_id,
            "block_id": info.block_id,
            "type": info.type,
            "ordinal": info.ordinal,
            "title": info.title,
            "parent_attachment_id": info.parent_attachment_id,
        }
        block["attachment_id"] = info.attachment_id
        return current_section_id

    def _detect_anchor(self, block: dict[str, Any]) -> AttachmentInfo | None:
        """Return attachment metadata when ``block`` represents an anchor."""
        if block.get("type") == "list_item":
            return None

        # Allow level 0 numbering (used for Schedule 1, Annex 1, etc.)
        # but skip blocks with deeper numbering levels
        if block.get("_docx_has_numbering"):
            list_meta = block.get("list")
            if isinstance(list_meta, Mapping):
                list_level = list_meta.get("level")
                if not isinstance(list_level, int) or list_level > 0:
                    return None
            else:
                # Has numbering flag but no list payload yet - check num_pr directly
                num_pr = block.get("num_pr")
                if isinstance(num_pr, dict):
                    ilvl = num_pr.get("ilvl", 0)
                    if ilvl > 0:
                        return None
                else:
                    return None

        list_meta = block.get("list")
        if isinstance(list_meta, Mapping):
            list_level = list_meta.get("level")
            if isinstance(list_level, int) and list_level > 0:
                return None

        heading_meta = block.get("heading") if isinstance(block.get("heading"), Mapping) else None
        source_text = heading_meta.get("text") if heading_meta and heading_meta.get("source") != "none" else None
        text = source_text or block.get("text") or ""
        parsed = self._parse_attachment_from_text(text)
        if parsed is None:
            return None

        attachment_type, ordinal, title = parsed
        parent_id = (
            self.current_attachment_id if attachment_type not in self._ROOT_TYPES else None
        )
        existing_level = block.get("level")
        if isinstance(existing_level, int):
            level = existing_level
        elif attachment_type in self._ROOT_TYPES:
            level = 1
        elif self._stack:
            level = self._stack[-1].level + 1
        else:
            level = 1

        return AttachmentInfo(
            attachment_id=str(uuid4()),
            block_id=block["id"],
            type=attachment_type,
            ordinal=ordinal,
            title=title,
            parent_attachment_id=parent_id,
            level=level if isinstance(level, int) else 1,
            from_heading=True,
        )

    def _detect_numbered_attachment(
        self,
        block: dict[str, Any],
        event: NumberingEvent | None,
    ) -> AttachmentInfo | None:
        if event is None:
            return None
        payload = event.payload
        level = payload.get("level")
        if not isinstance(level, int) or level != 0:
            return None
        group_id = event.restart_group_id
        if not isinstance(group_id, str):
            return None

        # First, check if the numbering pattern indicates an attachment type
        # (e.g., "Schedule %1", "Annex %1", "Exhibit %1")
        attachment_type = None
        pattern = payload.get("pattern") or ""
        for cue in ATTACHMENT_PATTERN_CUES:
            if cue.pattern.search(str(pattern)):
                attachment_type = cue.attachment_type
                break

        # Also check the block text for attachment keywords
        parsed = self._parse_attachment_from_text(block.get("text", ""))
        if parsed is None and self._pending_heading_text:
            parsed = self._parse_attachment_from_text(self._pending_heading_text)
        if parsed is not None:
            attachment_type = parsed[0]

        if attachment_type is None:
            return None

        # For attachment-type numbering (Schedule, Annex, etc.), each numbered item
        # at level 0 is a separate attachment, regardless of restart_boundary.
        # Only apply the group/restart checks for non-attachment numbering.
        is_attachment_pattern = attachment_type in self._ROOT_TYPES or attachment_type is not None
        
        if not is_attachment_pattern:
            # For regular numbered lists, use the original restart logic
            if group_id in self._processed_groups:
                return None
            ordinal_position = payload.get("ordinal_at_parse")
            if not payload.get("restart_boundary", False) and ordinal_position not in (None, 1):
                return None

        if parsed is not None:
            _, ordinal, title = parsed
        else:
            ordinal = _normalise_ordinal_token(str(payload.get("ordinal") or ""))
            title = None
            title = None

        parent_id = (
            self.current_attachment_id if attachment_type not in self._ROOT_TYPES else None
        )
        if attachment_type in self._ROOT_TYPES:
            level_value = 1
        elif self._stack:
            level_value = self._stack[-1].level + 1
        else:
            level_value = 1
        return AttachmentInfo(
            attachment_id=str(uuid4()),
            block_id=block["id"],
            type=attachment_type,
            ordinal=ordinal,
            title=title,
            parent_attachment_id=parent_id,
            level=level_value,
            group_id=group_id,
            from_heading=False,
        )

    def _parse_attachment_from_text(self, text: str | None) -> tuple[str, str | None, str | None] | None:
        if not text:
            return None
        candidate = text.strip()
        if not candidate:
            return None
        first_token = re.match(r"[A-Za-z]{3,}", candidate)
        if not first_token:
            return None
        keyword = first_token.group(0).casefold()
        attachment_type = ATTACHMENT_KEYWORDS.get(keyword)
        if attachment_type is None:
            return None

        raw_remainder = candidate[first_token.end() :].lstrip()
        ordinal, title = _parse_attachment_remainder(raw_remainder)
        if ordinal is None:
            return None
        return attachment_type, ordinal, title


def _parse_attachment_remainder(remainder: str) -> tuple[str | None, str | None]:
    """Parse the ordinal and title portion that follows an attachment keyword."""
    remainder = remainder.lstrip(ATTACHMENT_PUNCTUATION + " ")
    if not remainder:
        return None, None

    token_match = re.match(r"^\(?([A-Za-z0-9]+|[IVXLCDM]+)\)?", remainder)
    ordinal: str | None = None
    rest = remainder
    if token_match:
        token = token_match.group(1)
        ordinal = _normalise_ordinal(token)
        rest = remainder[token_match.end() :].lstrip(ATTACHMENT_PUNCTUATION + " ")

    title = rest.strip() or None
    return ordinal, title


def _normalise_ordinal(raw: str) -> str | None:
    """Normalise numeric, alphabetic, or roman-numeral ordinals."""
    if raw.isdigit():
        return raw.lstrip("0") or "0"
    upper = raw.upper()
    if re.fullmatch(r"[IVXLCDM]+", upper):
        return upper
    if len(raw) == 1 and raw.isalpha():
        return upper
    return None


def _normalise_ordinal_token(token: str) -> str | None:
    """Extract and normalise an ordinal from a token like 'Schedule 1' or '1'."""
    cleaned = token.strip().strip(ATTACHMENT_PUNCTUATION + ". ")
    if not cleaned:
        return None
    
    # Try direct normalisation first (for tokens like "1", "A", "IV")
    direct = _normalise_ordinal(cleaned)
    if direct is not None:
        return direct
    
    # For patterns like "Schedule 1", extract the trailing ordinal
    parts = cleaned.split()
    if len(parts) >= 2:
        # Check if last part is an ordinal
        last_ordinal = _normalise_ordinal(parts[-1])
        if last_ordinal is not None:
            return last_ordinal
    
    return None
