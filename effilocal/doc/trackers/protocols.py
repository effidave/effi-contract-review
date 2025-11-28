"""Protocol definitions for tracker interfaces."""

from __future__ import annotations

from typing import Protocol


class AttachmentTrackerProtocol(Protocol):
    """Interface for trackers that manage attachment metadata."""

    def apply(self, block: dict[str, object], current_section_id: str) -> tuple[str, bool]:
        """Assign attachment metadata to ``block`` and return the active section id."""

    def apply_to_table_block(self, block: dict[str, object]) -> None:
        """Propagate the current attachment id onto a table cell block."""

    def reset(self) -> None:
        """Clear any cached attachment state."""


class DefinitionTrackerProtocol(Protocol):
    """Interface for trackers that mark definition terms and bodies."""

    def observe_heading(self, text: str, level: int | None) -> None:
        """Observe a heading to decide whether definition mode is active."""

    def handle_blank(self) -> None:
        """Handle a blank line within a definition section."""

    def annotate_paragraph(self, block: dict[str, object], text: str) -> None:
        """Annotate a paragraph block with definition metadata when applicable."""

    def annotate_table_row(self, row_blocks: list[dict[str, object]]) -> None:
        """Annotate a table row representing a definition term/body pair."""

    def reset(self) -> None:
        """Reset tracking state."""


class DraftingNoteHelperProtocol(Protocol):
    """Interface for helpers that classify drafting-note text."""

    def looks_like_drafting_note(self, text: str) -> bool:
        """Return ``True`` when ``text`` matches a drafting-note pattern."""

    def assign_role(self, block: dict[str, object], text: str) -> None:
        """Assign the drafting-note role to ``block`` when appropriate."""


class NumberingTrackerProtocol(Protocol):
    """Interface for trackers that manage numbering payloads."""

    def reset_for_attachment(self) -> None:
        """Reset numbering state when entering a new attachment."""

    def next_for_paragraph(self, block: dict[str, object]) -> tuple[dict[str, object], str | None] | tuple[None, None]:
        """Produce numbering metadata for ``block`` when it participates in a list."""

    def paragraph_has_numbering(self, block: dict[str, object]) -> bool:
        """Return ``True`` when ``block`` carries numbering metadata."""

    def reset(self) -> None:
        """Reset the internal state completely."""


class TocFieldTrackerProtocol(Protocol):
    """Interface for trackers that synthesise TOC-derived numbering."""

    def synthesize(self, paragraph: Paragraph):
        """Build a numbering payload for a TOC field paragraph if one exists."""

    def reset(self) -> None:
        """Reset TOC tracking state."""
