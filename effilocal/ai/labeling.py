"""OpenAI labeling client stubs for Sprint 2."""

from __future__ import annotations

import json
import os
import time
from collections.abc import Iterable, Mapping
from jsonschema import Draft7Validator
from typing import Any, Literal, Protocol

from effilocal.config.logging import get_logger
from pydantic import BaseModel, ConfigDict, Field

ResultTuple = tuple[dict[str, Any], dict[str, Any]]
TransportResult = str | tuple[str, Mapping[str, Any]]


class TransportCallable(Protocol):
    def __call__(
        self,
        *,
        system: str,
        payload: Mapping[str, Any],
        schema: Mapping[str, Any] | None,
    ) -> TransportResult:
        ...

USE_REAL_API_ENV = "USE_REAL_API"
OPENAI_API_KEY_ENV = "OPENAI_API_KEY"
DEFAULT_MODEL = "gpt-4o-2024-08-06"
DEFAULT_TEMPERATURE = 0.2
RESPONSE_SCHEMA_NAME = "doc_labels"

LOGGER = get_logger("effilocal.ai.labeling")


class _LabelEntry(BaseModel):
    """Pydantic model mirroring schemas/labels.schema.json label entries."""

    model_config = ConfigDict(extra="forbid")

    section_id: str
    role: Literal[
        "title",
        "abstract",
        "intro",
        "methods",
        "results",
        "discussion",
        "conclusion",
        "appendix",
        "boilerplate",
        "unsure",
    ]
    topics: list[str]
    entities: list[str] | None = None
    notes: str | None = None


class _DocLabels(BaseModel):
    """Pydantic model for the top-level document labels response."""

    model_config = ConfigDict(extra="forbid")

    doc_id: str
    confidence: float = Field(ge=0.0, le=1.0)
    labels: list[_LabelEntry]


def run_labeling(
    *,
    system: str,
    payload: Mapping[str, Any],
    transport: Any | None = None,
    schema: Mapping[str, Any] | None = None,
    section_lookup: set[str] | None = None,
) -> ResultTuple:
    """Invoke the transport, parse JSON response, and return metadata."""

    if transport is None:
        raise ValueError("transport callable must be provided for run_labeling")

    def _format_for_log(obj: Any) -> str:
        if isinstance(obj, (bytes, bytearray)):
            try:
                return obj.decode('utf-8')
            except UnicodeDecodeError:
                return repr(obj)
        if isinstance(obj, str):
            return obj
        try:
            return json.dumps(obj, ensure_ascii=False)
        except TypeError:
            return repr(obj)

    def _log_response_summary(result_payload: Mapping[str, Any], meta_payload: Mapping[str, Any]) -> None:
        doc_id = result_payload.get("doc_id", "unknown")
        labels = result_payload.get("labels")
        label_count = len(labels) if isinstance(labels, list) else 0
        errors = meta_payload.get("error")
        if isinstance(errors, list):
            error_count = len(errors)
        elif errors:
            error_count = 1
        else:
            error_count = 0
        elapsed = meta_payload.get("elapsed_sec")
        elapsed_value = float(elapsed) if isinstance(elapsed, (int, float)) else 0.0
        LOGGER.info(
            "Labeling completed doc_id=%s labels=%d errors=%d elapsed=%.3fs",
            doc_id,
            label_count,
            error_count,
            elapsed_value,
        )

    LOGGER.debug("Labeling request payload: %s", _format_for_log(payload))
    start = time.perf_counter()
    response = transport(system=system, payload=payload, schema=schema)
    transport_meta: Any | None = None

    if isinstance(response, tuple) and len(response) == 2:
        response, transport_meta = response
    elapsed = time.perf_counter() - start
    if isinstance(response, (bytes, bytearray)):
        response = response.decode("utf-8")

    LOGGER.debug("Labeling raw response: %s", _format_for_log(response))
    if isinstance(response, str):
        cleaned_response = _strip_json_markdown_fence(response.strip())
        result: dict[str, Any] = json.loads(cleaned_response)
    else:
        result = dict(response)

    usage_info: Any | None = None
    if transport_meta is not None:
        if isinstance(transport_meta, Mapping):
            usage_info = transport_meta.get("usage")
        else:
            usage_info = getattr(transport_meta, "usage", None)

        if isinstance(usage_info, Mapping):
            usage_info = dict(usage_info)

    if isinstance(result, dict) and "usage" in result:
        result_usage = result.pop("usage")
        if isinstance(result_usage, Mapping):
            result_usage = dict(result_usage)

        if usage_info is None:
            usage_info = result_usage
        elif isinstance(usage_info, Mapping) and isinstance(result_usage, Mapping):
            combined = dict(result_usage)
            combined.update(usage_info)
            usage_info = combined
        else:
            usage_info = usage_info or result_usage

    meta: dict[str, Any] = {"elapsed_sec": elapsed}
    if usage_info is not None:
        meta["usage"] = usage_info

    if schema is not None:
        validator = Draft7Validator(schema)
        schema_errors = sorted(validator.iter_errors(result), key=lambda err: err.path)
        if schema_errors:
            for error in schema_errors:
                meta.setdefault("error", []).append(f"Schema violation at {_format_schema_path(error)}: {error.message}")
            LOGGER.debug("Labeling parsed result: %s", _format_for_log(result))
            LOGGER.debug("Labeling meta: %s", _format_for_log(meta))
            _log_response_summary(result, meta)
            return result, meta

    if section_lookup:
        missing_sections = _find_missing_sections(result.get("labels", []), section_lookup)
        if missing_sections:
            meta.setdefault("error", []).extend(
                f"Unknown section_id: {section_id}" for section_id in sorted(missing_sections)
            )
            LOGGER.debug("Labeling parsed result: %s", _format_for_log(result))
            LOGGER.debug("Labeling meta: %s", _format_for_log(meta))
            _log_response_summary(result, meta)
            return result, meta

    LOGGER.debug("Labeling parsed result: %s", _format_for_log(result))
    LOGGER.debug("Labeling meta: %s", _format_for_log(meta))
    _log_response_summary(result, meta)
    return result, meta


def build_section_lookup(outline: Iterable[Mapping[str, Any]]) -> set[str]:
    """Return unique section identifiers from the outline."""

    section_ids: set[str] = set()
    for entry in outline:
        section_id = entry.get("section_id")
        if isinstance(section_id, str) and section_id:
            section_ids.add(section_id)
    return section_ids


def _find_missing_sections(
    labels: Iterable[Mapping[str, Any]],
    section_lookup: set[str],
) -> set[str]:
    """Collect section IDs from labels that are not present in the lookup."""

    missing: set[str] = set()
    for label in labels or []:
        section_id = label.get("section_id")
        if isinstance(section_id, str) and section_id and section_id not in section_lookup:
            missing.add(section_id)
    return missing


def _format_schema_path(error: Any) -> str:
    """Return dotted JSON path (with indices) for a validation error."""

    path = list(error.path) if hasattr(error, "path") else []
    if not path:
        return "<root>"

    formatted: list[str] = []
    for part in path:
        if isinstance(part, int):
            if formatted:
                formatted[-1] = f"{formatted[-1]}[{part}]"
            else:
                formatted.append(f"[{part}]")
        else:
            formatted.append(str(part))
    return ".".join(formatted)


def _strip_json_markdown_fence(text: str) -> str:
    """Remove surrounding Markdown code fences when present."""

    if not text.startswith("```"):
        return text

    lines = text.splitlines()
    if not lines:
        return text

    first_line = lines[0].strip()
    if first_line.startswith("```"):
        lines = lines[1:]

    for idx in range(len(lines) - 1, -1, -1):
        if lines[idx].strip() == "```":
            lines = lines[:idx]
            break

    return "\n".join(lines).strip()


def should_use_real_api() -> bool:
    """Return True when the real OpenAI transport should be invoked."""

    return os.getenv(USE_REAL_API_ENV) == "1"


def create_openai_transport(
    *,
    model: str = DEFAULT_MODEL,
    temperature: float = DEFAULT_TEMPERATURE,
) -> TransportCallable:
    """Build a callable that proxies requests to the OpenAI Responses API.

    The transport serialises the payload as JSON and requests schema-constrained
    output. Usage metadata from the OpenAI response is preserved.
    """

    api_key = os.getenv(OPENAI_API_KEY_ENV)
    if not api_key:
        raise RuntimeError(
            f"Cannot use real API without {OPENAI_API_KEY_ENV} set in the environment."
        )

    client: Any = _build_openai_client(api_key)

    def _transport(
        *,
        system: str,
        payload: Mapping[str, Any],
        schema: Mapping[str, Any] | None,
    ) -> tuple[str, dict[str, Any]]:
        text_format = _build_response_format(schema)
        user_payload = json.dumps(payload, ensure_ascii=False)

        request_kwargs: dict[str, Any] = {
            "model": model,
            "temperature": temperature,
            "instructions": system,
            "input": user_payload,
        }

        # Remove None values to satisfy the API contract.
        clean_kwargs = {key: value for key, value in request_kwargs.items() if value is not None}
        try:
            if text_format is not None:
                response = client.responses.parse(text_format=text_format, **clean_kwargs)
                parsed_payload = getattr(response, "output_parsed", None)
                if parsed_payload is None:
                    raise RuntimeError(
                        "Structured output response did not include parsed content; cannot continue without schema-validated data."
                    )
                output_text = json.dumps(
                    parsed_payload.model_dump(exclude_none=True), ensure_ascii=False
                )
            else:
                response = client.responses.create(**clean_kwargs)
                output_text = _extract_output_text(response)
        except TypeError as exc:
            raise RuntimeError(
                "OpenAI responses API rejected structured output parameters; verify openai-python version supports "
                "responses.parse structured outputs."
            ) from exc

        usage = _extract_usage(getattr(response, "usage", None))
        meta: dict[str, Any] = {}
        if usage is not None:
            meta["usage"] = usage
        return output_text, meta

    return _transport


def _build_response_format(schema: Mapping[str, Any] | None) -> type[_DocLabels] | None:
    if schema is None:
        return None
    schema_id = schema.get("$id")
    title = schema.get("title")
    if title == "DocLabels" or (isinstance(schema_id, str) and schema_id.endswith("labels.schema.json")):
        return _DocLabels
    raise ValueError(
        "OpenAI transport received an unexpected schema. Structured Outputs require the DocLabels schema."
    )


def _extract_output_text(response: Any) -> str:
    if response is None:
        raise RuntimeError("OpenAI response is empty.")

    output_text = getattr(response, "output_text", None)
    if output_text:
        return output_text

    output = getattr(response, "output", None)
    if isinstance(output, list) and output:
        first = output[0]
        content = getattr(first, "content", None)
        if isinstance(content, list) and content:
            item = content[0]
            text = getattr(item, "text", None)
            if text:
                return text
            if isinstance(item, Mapping):
                text = item.get("text")
                if text:
                    return str(text)

    if hasattr(response, "data") and isinstance(response.data, list) and response.data:
        datum = response.data[0]
        if hasattr(datum, "content"):
            content = datum.content
            if isinstance(content, list) and content:
                text = getattr(content[0], "text", None)
                if text:
                    return text

    raise RuntimeError("Unable to extract text from OpenAI response.")


def _extract_usage(usage_obj: Any) -> dict[str, Any] | None:
    if usage_obj is None:
        return None

    tokens: dict[str, Any] = {}
    for key in ("input_tokens", "output_tokens"):
        if isinstance(usage_obj, Mapping):
            value = usage_obj.get(key)
        else:
            value = getattr(usage_obj, key, None)
        if value is not None:
            tokens[key] = value
    return tokens or None


def _build_openai_client(api_key: str) -> Any:
    from openai import OpenAI  # Imported lazily to avoid hard dependency when unused.

    return OpenAI(api_key=api_key)
