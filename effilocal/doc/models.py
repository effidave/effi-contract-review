"""Data models shared across Effi-Local components."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, MutableMapping
from uuid import uuid4


@dataclass
class Block:
    """Minimal representation of a document block."""

    uuid: str
    content_hash: str
    type: str
    text: str = ""


@dataclass(eq=True, frozen=False)
class TagRange:
    """
    In-memory representation of a tag range.

    Mirrors the structure defined in ``tag_range.schema.json``.
    """

    id: str
    label: str
    start_marker_id: str
    end_marker_id: str
    status: str = "active"
    attributes: MutableMapping[str, Any] | None = None
    anchors: MutableMapping[str, Any] | None = None
    created_at: str | None = None
    updated_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert the tag range into a JSON-serialisable dictionary."""

        payload: dict[str, Any] = {
            "id": self.id,
            "label": self.label,
            "start_marker_id": self.start_marker_id,
            "end_marker_id": self.end_marker_id,
            "status": self.status,
        }

        if self.attributes is not None:
            payload["attributes"] = dict(self.attributes)
        if self.anchors is not None:
            payload["anchors"] = dict(self.anchors)
        if self.created_at is not None:
            payload["created_at"] = self.created_at
        if self.updated_at is not None:
            payload["updated_at"] = self.updated_at

        return payload

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> TagRange:
        """Create a ``TagRange`` instance from a dictionary."""

        return cls(
            id=data["id"],
            label=data["label"],
            start_marker_id=data["start_marker_id"],
            end_marker_id=data["end_marker_id"],
            status=data.get("status", "active"),
            attributes=dict(data["attributes"]) if "attributes" in data else None,
            anchors=dict(data["anchors"]) if "anchors" in data else None,
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )


def make_block_range(block_uuid: str) -> dict[str, Any]:
    """
    Return a JSON-ready block tag range for the supplied block UUID.

    The helper produces fresh UUIDs for the range itself and its start/end
    markers, with ``status`` defaulting to ``"active"``. The result matches the
    structure described in ``tag_range.schema.json`` for ``label == "block"``.
    """

    tag_range = TagRange(
        id=str(uuid4()),
        label="block",
        start_marker_id=str(uuid4()),
        end_marker_id=str(uuid4()),
        status="active",
        attributes={"block_id": block_uuid},
    )
    return tag_range.to_dict()
