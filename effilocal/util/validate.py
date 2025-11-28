"""Cross-artifact validation helpers."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from effilocal.config.logging import get_logger
from effilocal.doc.manifest import collect_schema_checksums

LOGGER = get_logger("effilocal.validate")


@dataclass(slots=True)
class ValidationIssue:
    """Represents a single validation problem."""

    code: str
    message: str
    context: Mapping[str, Any] | None = None


@dataclass(slots=True)
class ValidationReport:
    """Aggregates validation issues across checks."""

    errors: list[ValidationIssue] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        """Return `True` when no errors were recorded."""

        return not self.errors

    def add(self, code: str, message: str, context: Mapping[str, Any] | None = None) -> None:
        LOGGER.debug(
            "Recording validation issue",
            extra={"code": code, "message": message, "context": dict(context or {})},
        )
        self.errors.append(ValidationIssue(code=code, message=message, context=context))


def validate_artifacts(
    *,
    blocks: Sequence[Mapping[str, Any]],
    sections: Mapping[str, Any],
    tag_ranges: Sequence[Mapping[str, Any]] | None = None,
    manifest: Mapping[str, Any] | None = None,
    schema_dir: Path | None = None,
) -> ValidationReport:
    """Perform cross-file validation and return a structured report."""

    report = ValidationReport()

    _check_uuid_uniqueness(blocks, sections, tag_ranges, report)
    _check_cross_references(blocks, sections, tag_ranges, report)
    _check_list_payload(blocks, report)

    if manifest is not None:
        if schema_dir is None:
            report.add("missing_schema_dir", "schema_dir must be provided when manifest is supplied.")
        else:
            _check_schema_checksums(manifest, schema_dir, report)

    return report


def _check_uuid_uniqueness(
    blocks: Sequence[Mapping[str, Any]],
    sections: Mapping[str, Any],
    tag_ranges: Sequence[Mapping[str, Any]] | None,
    report: ValidationReport,
) -> None:
    seen: Counter[tuple[str, str]] = Counter()

    for block in blocks:
        block_id = block.get("id")
        if isinstance(block_id, str) and block_id:
            seen[("block", block_id)] += 1

    for node in _iter_sections(sections):
        section_id = node.get("id")
        if isinstance(section_id, str) and section_id:
            seen[("section", section_id)] += 1

    if tag_ranges:
        for rng in tag_ranges:
            range_id = rng.get("id")
            if isinstance(range_id, str) and range_id:
                seen[("tag_range", range_id)] += 1
            start_id = rng.get("start_marker_id")
            if isinstance(start_id, str) and start_id:
                seen[("marker", start_id)] += 1
            end_id = rng.get("end_marker_id")
            if isinstance(end_id, str) and end_id:
                seen[("marker", end_id)] += 1

    for (kind, identifier), count in seen.items():
        if count > 1:
            LOGGER.error(
                "Duplicate UUID detected",
                extra={"kind": kind, "id": identifier, "count": count},
            )
            report.add(
                "duplicate_uuid",
                f"Duplicate {kind} UUID detected: {identifier}",
                {"id": identifier, "kind": kind, "count": count},
            )


def _check_cross_references(
    blocks: Sequence[Mapping[str, Any]],
    sections: Mapping[str, Any],
    tag_ranges: Sequence[Mapping[str, Any]] | None,
    report: ValidationReport,
) -> None:
    section_ids = {node.get("id") for node in _iter_sections(sections)}
    block_ids = {block.get("id") for block in blocks}

    for block in blocks:
        section_id = block.get("section_id")
        if section_id and section_id not in section_ids:
            report.add(
                "unknown_section_id",
                "Block references unknown section_id",
                {"block_id": block.get("id"), "section_id": section_id},
            )

    if not tag_ranges:
        return

    for rng in tag_ranges:
        attrs = rng.get("attributes")
        if isinstance(attrs, Mapping):
            block_id = attrs.get("block_id")
            if block_id and block_id not in block_ids:
                report.add(
                    "unknown_block_in_range",
                    "Tag range references missing block",
                    {"range_id": rng.get("id"), "block_id": block_id},
                )
        for anchor_key in ("start", "end"):
            anchor = rng.get("anchors", {}).get(anchor_key)
            if isinstance(anchor, Mapping):
                near_id = anchor.get("near_block_id")
                if near_id and near_id not in block_ids:
                    report.add(
                        "unknown_anchor_block",
                        "Anchor references missing block",
                        {
                            "range_id": rng.get("id"),
                            "anchor": anchor_key,
                            "near_block_id": near_id,
                        },
                    )


def _check_schema_checksums(
    manifest: Mapping[str, Any],
    schema_dir: Path,
    report: ValidationReport,
) -> None:
    recorded = manifest.get("schema_checksums")
    if not isinstance(recorded, Mapping):
        report.add("schema_checksums_missing", "Manifest is missing schema_checksums map.")
        return

    actual = collect_schema_checksums(schema_dir)

    missing = {name for name in actual if name not in recorded}
    extra = {name for name in recorded if name not in actual}
    mismatched: list[tuple[str, tuple[str, str]]] = []

    for name, digest in actual.items():
        recorded_digest = recorded.get(name)
        if recorded_digest and recorded_digest != digest:
            mismatched.append((name, (recorded_digest, digest)))

    for name in missing:
        report.add(
            "schema_checksum_missing",
            "Schema checksum missing from manifest",
            {"schema": name},
        )

    for name in extra:
        report.add(
            "schema_checksum_extra",
            "Manifest lists schema not present on disk",
            {"schema": name},
        )

    for name, (recorded_digest, actual_digest) in mismatched:
        report.add(
            "schema_checksum_mismatch",
            "Recorded schema checksum differs from actual file",
            {
                "schema": name,
                "manifest_digest": recorded_digest,
                "actual_digest": actual_digest,
            },
        )


def _iter_sections(sections: Mapping[str, Any]) -> Iterable[Mapping[str, Any]]:
    root = sections.get("root", {})
    yield from _walk_section_nodes(root)


def _walk_section_nodes(node: Mapping[str, Any]) -> Iterable[Mapping[str, Any]]:
    for child in node.get("children", []):
        yield child
        yield from _walk_section_nodes(child)


def _check_list_payload(
    blocks: Sequence[Mapping[str, Any]],
    report: ValidationReport,
) -> None:
    """Validate numbering-related payloads on blocks."""

    for block in blocks:
        list_payload = block.get("list")
        if not isinstance(list_payload, Mapping):
            continue

        counters = list_payload.get("counters")
        level = list_payload.get("level")

        if isinstance(level, int) and isinstance(counters, Sequence):
            expected = level + 1
            if len(counters) != expected:
                report.add(
                    "invalid_list_counters",
                    "List counters length does not match level + 1",
                    {
                        "block_id": block.get("id"),
                        "level": level,
                        "counters": list(counters),
                    },
                )

