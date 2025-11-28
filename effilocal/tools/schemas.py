"""Helpers for loading and validating tool JSON schemas."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from jsonschema import Draft7Validator, ValidationError

SCHEMA_ROOT = Path(__file__).resolve().parents[2] / "schemas" / "tools"

_INPUT_SCHEMA_FILES: Mapping[str, str] = {
    "get_doc_outline": "get_doc_outline.input.schema.json",
    "get_content_by_range": "get_content_by_range.input.schema.json",
    "get_section": "get_section.input.schema.json",
    "get_related_units": "get_related_units.input.schema.json",
    "get_by_tag": "get_by_tag.input.schema.json",
    "get_by_clause_number": "get_by_clause_number.input.schema.json",
}

_OUTPUT_SCHEMA_FILES: Mapping[str, str] = {
    "get_doc_outline": "get_doc_outline.output.schema.json",
    "get_content_by_range": "get_content_by_range.output.schema.json",
    "get_section": "get_section.output.schema.json",
    "get_related_units": "get_related_units.output.schema.json",
    "get_by_tag": "get_by_tag.output.schema.json",
    "get_by_clause_number": "get_by_clause_number.output.schema.json",
}

SchemaKind = str


class SchemaValidationError(ValueError):
    """Raised when a tool payload fails schema validation."""


def get_input_schema(tool_name: str) -> dict[str, Any]:
    """Return the JSON schema dictionary for a tool's input payload."""
    return _load_schema(_INPUT_SCHEMA_FILES, tool_name)


def get_output_schema(tool_name: str) -> dict[str, Any]:
    """Return the JSON schema dictionary for a tool's output payload."""
    return _load_schema(_OUTPUT_SCHEMA_FILES, tool_name)


def validate_tool_input(tool_name: str, payload: Mapping[str, Any] | None) -> None:
    """Validate a tool input payload against the corresponding JSON schema."""
    _validate(tool_name, payload, _INPUT_SCHEMA_FILES)


def validate_tool_output(tool_name: str, payload: Mapping[str, Any] | None) -> None:
    """Validate a tool output payload against the corresponding JSON schema."""
    _validate(tool_name, payload, _OUTPUT_SCHEMA_FILES)


def _validate(
    tool_name: str,
    payload: Mapping[str, Any] | None,
    schema_files: Mapping[str, str],
) -> None:
    schema_filename = schema_files.get(tool_name)
    if schema_filename is None:
        raise ValueError(f"Unknown tool: {tool_name}")

    validator = _get_validator(schema_filename)
    instance = payload or {}
    errors = sorted(
        validator.iter_errors(instance),
        key=lambda error: list(error.absolute_path),
    )
    if not errors:
        return

    message = "; ".join(_format_error(error) for error in errors)
    raise SchemaValidationError(message)


def _load_schema(schema_files: Mapping[str, str], tool_name: str) -> dict[str, Any]:
    schema_filename = schema_files.get(tool_name)
    if schema_filename is None:
        raise ValueError(f"Unknown tool: {tool_name}")
    return dict(_get_schema_from_disk(schema_filename))


@lru_cache(maxsize=None)
def _get_schema_from_disk(filename: str) -> dict[str, Any]:
    path = SCHEMA_ROOT / filename
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


@lru_cache(maxsize=None)
def _get_validator(filename: str) -> Draft7Validator:
    schema = _get_schema_from_disk(filename)
    return Draft7Validator(schema)


def _format_error(error: ValidationError) -> str:
    path = _format_path(error.absolute_path)
    message = error.message
    if error.validator == "required":
        missing = _extract_required_property(error)
        if missing and path == "root":
            path = missing
            message = "is a required property"
        elif missing:
            message = f"{missing!r} is a required property"
    if path and path != "root":
        return f"{path}: {message}"
    return message


def _format_path(path: Sequence[Any]) -> str:
    if not path:
        return "root"
    parts: list[str] = []
    for part in path:
        if isinstance(part, int):
            if not parts:
                parts.append(f"[{part}]")
            else:
                parts[-1] = f"{parts[-1]}[{part}]"
        else:
            parts.append(str(part))
    return ".".join(parts)


def _extract_required_property(error: ValidationError) -> str | None:
    if error.validator != "required":
        return None
    validator_value = error.validator_value
    if isinstance(validator_value, Iterable):
        for candidate in validator_value:
            if isinstance(candidate, str) and candidate in error.message:
                return candidate
    if "'" in error.message:
        parts = error.message.split("'")
        if len(parts) >= 3:
            return parts[1]
    return None
