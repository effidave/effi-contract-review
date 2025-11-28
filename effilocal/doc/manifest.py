"""Helpers for building manifest metadata."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from effilocal.doc.constants import DEFAULT_FALLBACK_HEADING_LABEL
from effilocal.util.hash import sha256_file


DEFAULT_SDT_CARRIER = "content-controls"
DEFAULT_RANGE_MARKER_PREFIX = "marker:"


def collect_schema_checksums(schema_dir: Path) -> dict[str, str]:
    """Return sha256 checksums for every ``*.schema.json`` file in ``schema_dir``."""

    checksums: dict[str, str] = {}
    for schema_path in sorted(schema_dir.glob("*.schema.json")):
        checksums[schema_path.name] = sha256_file(schema_path)
    return checksums


def build_manifest(
    *,
    doc_id: str,
    tool_version: str,
    checksums: Mapping[str, str],
    schema_dir: Path,
    version: int = 1,
    created_at: str | None = None,
    doc_format: str = "docx",
    sdt_carrier: str = DEFAULT_SDT_CARRIER,
    range_marker_carrier: str = DEFAULT_SDT_CARRIER,
    range_marker_tag_prefix: str = DEFAULT_RANGE_MARKER_PREFIX,
    fallback_heading_label: str = DEFAULT_FALLBACK_HEADING_LABEL,
    attachments: list[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Construct the manifest payload for ``manifest.json``."""

    timestamp = created_at or _utc_timestamp()
    schema_checksums = collect_schema_checksums(schema_dir)

    manifest: dict[str, Any] = {
        "doc_id": doc_id,
        "v": version,
        "created_at": timestamp,
        "tool_version": tool_version,
        "doc_format": doc_format,
        "sdt_carrier": sdt_carrier,
        "range_marker_carrier": range_marker_carrier,
        "range_marker_tag_prefix": range_marker_tag_prefix,
        "fallback_heading_label": fallback_heading_label,
        "checksums": dict(checksums),
        "schema_checksums": schema_checksums,
    }
    if attachments is not None:
        manifest["attachments"] = [dict(entry) for entry in attachments]
    return manifest


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
