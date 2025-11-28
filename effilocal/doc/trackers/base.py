"""Shared tracker base classes."""

from __future__ import annotations

from effilocal.doc.numbering_context import NumberingEvent


class TrackerEventConsumer:
    """Optional mixin for trackers that listen to shared events."""

    def on_numbering_event(self, event: NumberingEvent) -> None:  # pragma: no cover - default no-op
        """Handle numbering events emitted by the pipeline."""
        return None

    def on_attachment_boundary(self, attachment_id: str) -> None:  # pragma: no cover - default no-op
        """Handle attachment boundary events if needed."""
        return None
