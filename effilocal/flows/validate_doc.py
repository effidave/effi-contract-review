"""Utilities for validating parsed document directories."""

from __future__ import annotations

import json
from json import JSONDecodeError
from jsonschema import Draft202012Validator
from pathlib import Path
from typing import Any, Mapping

from effilocal.util import validate as cross_validate

SCHEMA_DIR = Path(__file__).resolve().parents[2] / "schemas"

_SCHEMA_MAP: dict[str, tuple[str, bool]] = {
    "blocks.jsonl": ("block.schema.json", True),
    "sections.json": ("sections.schema.json", False),
    "styles.json": ("styles.schema.json", False),
    "index.json": ("index.schema.json", False),
    "manifest.json": ("manifest.schema.json", False),
    "relationships.json": ("relationships.schema.json", False),
    "tag_ranges.jsonl": ("tag_range.schema.json", True),
}


def _load_schema(name: str) -> dict[str, Any]:
    schema_path = SCHEMA_DIR / name
    return json.loads(schema_path.read_text(encoding="utf-8"))


def validate_directory(data_dir: Path, *, deep: bool = False) -> cross_validate.ValidationReport:
    report, artifacts = _quick_validate(data_dir)
    if deep and report.ok:
        deep_report = cross_validate.validate_artifacts(
            blocks=artifacts.get("blocks", []),
            sections=artifacts.get("sections", {}),
            tag_ranges=artifacts.get("tag_ranges"),
            manifest=artifacts.get("manifest"),
            schema_dir=SCHEMA_DIR,
        )
        report.errors.extend(deep_report.errors)
    return report


def _quick_validate(
    data_dir: Path,
) -> tuple[cross_validate.ValidationReport, dict[str, Any]]:
    report = cross_validate.ValidationReport()
    artifacts: dict[str, Any] = {}

    for filename, (schema_name, is_jsonl) in _SCHEMA_MAP.items():
        path = data_dir / filename
        optional = filename == "tag_ranges.jsonl"
        if not path.exists():
            if optional:
                continue
            report.add("missing_artifact", f"Required artifact missing: {filename}")
            continue

        try:
            data: Any
            if is_jsonl:
                data = _load_jsonl(path)
            else:
                data = json.loads(path.read_text(encoding="utf-8"))
        except JSONDecodeError as exc:
            report.add(
                "invalid_json",
                f"Could not parse {filename}: {exc.msg}",
                {"filename": filename, "lineno": exc.lineno, "colno": exc.colno},
            )
            continue

        schema = _load_schema(schema_name)
        validator = Draft202012Validator(schema)
        error_count_before = len(report.errors)

        if is_jsonl:
            for index, item in enumerate(data):
                for error in validator.iter_errors(item):
                    report.add(
                        "schema_validation_error",
                        f"{filename} line {index + 1}: {error.message}",
                        {"filename": filename, "index": index, "path": list(error.path)},
                    )
        else:
            for error in validator.iter_errors(data):
                report.add(
                    "schema_validation_error",
                    f"{filename}: {error.message}",
                    {"filename": filename, "path": list(error.path)},
                )

        if len(report.errors) == error_count_before:
            key = filename.replace(".jsonl", "").replace(".json", "")
            artifacts[key] = data

    artifacts.setdefault("tag_ranges", None)
    artifacts.setdefault("manifest", None)
    return report, artifacts


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        try:
            entry = json.loads(stripped)
        except JSONDecodeError as exc:
            raise JSONDecodeError(exc.msg, exc.doc, exc.pos) from None
        if not isinstance(entry, Mapping):
            raise JSONDecodeError("JSONL entry must be an object", stripped, 0)
        entries.append(dict(entry))
    return entries
