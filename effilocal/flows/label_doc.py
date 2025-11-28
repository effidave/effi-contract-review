"""Labeling flow helpers for Sprint 2."""

from __future__ import annotations

import json
from collections import OrderedDict
from collections.abc import Iterable, Iterator, Mapping
from pathlib import Path
from typing import Any, Callable

from effilocal.ai.labeling import (
    DEFAULT_TEMPERATURE,
    build_section_lookup,
    create_openai_transport,
    run_labeling,
    should_use_real_api,
)
from effilocal.ai.prompts import build_labeling_prompt
from effilocal.util.io import iter_jsonl
from effilocal.util.redact import redact_snippets

SCHEMA_DIR = Path(__file__).resolve().parents[2] / "schemas"
LABELS_SCHEMA_PATH = SCHEMA_DIR / "labels.schema.json"
BATCH_SECTION_LIMIT = 40


class LabelingError(RuntimeError):
    """Raised when the labeling flow cannot complete."""


class PayloadBudgetExceeded(RuntimeError):
    """Raised when a payload exceeds the configured character budget."""

    def __init__(self, payload_size: int, max_chars: int):
        super().__init__(
            f"Labeling payload is {payload_size} characters which exceeds the "
            f"configured limit of {max_chars} characters."
        )
        self.payload_size = payload_size
        self.max_chars = max_chars


def label(
    doc_id: str,
    *,
    data_dir: Path,
    debug: bool = False,
    transport: Any | None = None,
    batch_section_limit: int | None = None,
    temperature: float | None = None,
    redact: bool = False,
    payload_max_chars: int | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Run the Sprint 2 labeling flow using stub transport."""

    doc_dir = Path(data_dir) / doc_id
    if not doc_dir.exists():
        raise LabelingError(f"Data directory not found for doc_id={doc_id}: {doc_dir}")

    sections_path = doc_dir / "sections.json"
    blocks_path = doc_dir / "blocks.jsonl"
    styles_path = doc_dir / "styles.json"

    outline = build_outline(sections_path, blocks_path)
    snippets = build_snippets(sections_path, blocks_path)
    if redact:
        snippets = redact_snippets(snippets)
    style_summary = load_style_summary(styles_path)
    section_lookup = build_section_lookup(outline)

    limit = batch_section_limit if batch_section_limit is not None else BATCH_SECTION_LIMIT
    run_temperature = DEFAULT_TEMPERATURE if temperature is None else temperature
    outline_batches = _split_outline(outline, limit)
    selected_transport = transport or _build_transport(run_temperature)
    schema = _load_labels_schema()
    debug_payload_content: dict[str, Any] | None = None

    batch_payloads: list[dict[str, Any]] | None = None

    try:
        if len(outline_batches) == 1:
            system_message, payload = build_labeling_prompt(
                doc_id,
                {
                    "outline": outline,
                    "snippets": snippets,
                    "style_summary": style_summary,
                },
            )
            _ensure_payload_budget(payload, payload_max_chars)
            result, meta = run_labeling(
                system=system_message,
                payload=payload,
                transport=selected_transport,
                schema=schema,
                section_lookup=section_lookup,
            )
            debug_payload_content = {
                "doc_id": doc_id,
                "outline": outline,
                "snippets": snippets,
                "style_summary": style_summary,
                "label_payload": payload,
                "temperature": run_temperature,
                "redact": redact,
                "payload_max_chars": payload_max_chars,
            }
        else:
            result, meta, batch_payloads = _run_batched_labeling(
                doc_id=doc_id,
                outline_batches=outline_batches,
                snippets=snippets,
                style_summary=style_summary,
                transport=selected_transport,
                schema=schema,
                section_lookup=section_lookup,
                payload_max_chars=payload_max_chars,
            )
            debug_payload_content = {
                "doc_id": doc_id,
                "outline": outline,
                "snippets": snippets,
                "style_summary": style_summary,
                "batches": batch_payloads,
                "temperature": run_temperature,
                "redact": redact,
                "payload_max_chars": payload_max_chars,
            }
    except PayloadBudgetExceeded as exc:
        message = (
            f"Labeling payload exceeds the configured character budget "
            f"({exc.payload_size} > {exc.max_chars}). "
            "Consider increasing --payload-max-chars or reducing snippet size."
        )
        result = {
            "doc_id": doc_id,
            "confidence": 0.0,
            "labels": [],
        }
        meta = {"elapsed_sec": 0.0, "error": [message]}
        debug_payload_content = {
            "doc_id": doc_id,
            "outline": outline,
            "style_summary": style_summary,
            "temperature": run_temperature,
            "redact": redact,
            "payload_budget": {
                "limit": exc.max_chars,
                "actual_chars": exc.payload_size,
            },
            "snippets": {
                section_id: "[omitted due to payload budget overflow]" for section_id in snippets
            },
        }

    labels_path = doc_dir / "labels.json"
    report_path = doc_dir / "label_report.json"

    _write_json(labels_path, result)

    errors = _normalize_errors(meta.get("error"))

    report = {
        "doc_id": doc_id,
        "errors": errors,
        "elapsed_sec": meta.get("elapsed_sec"),
        "usage": meta.get("usage"),
    }
    _write_json(report_path, report)

    if debug and debug_payload_content is not None:
        write_debug_payload(doc_dir, debug_payload_content)

    if errors:
        message = errors[0] if errors else "unknown error"
        raise LabelingError(
            f"Labeling produced {len(errors)} error(s); see {report_path.name}: {message}"
        )

    return result, report


def build_outline(
    sections_path: Path,
    blocks_path: Path,
) -> list[dict[str, Any]]:
    """Construct outline entries with block and character counts."""

    sections = json.loads(Path(sections_path).read_text(encoding="utf-8"))
    blocks_by_id = {block["id"]: block for block in _iter_blocks(blocks_path)}

    outline: list[dict[str, Any]] = []
    for node in _iter_section_nodes(sections.get("root", {})):
        block_ids = node.get("block_ids", [])
        texts = [blocks_by_id.get(block_id, {}).get("text", "") for block_id in block_ids]
        outline.append(
            {
                "section_id": node.get("id"),
                "title": node.get("title"),
                "level": node.get("level"),
                "block_count": len(block_ids),
                "char_count": sum(len(text or "") for text in texts),
            }
        )
    return outline


def build_snippets(
    sections_path: Path,
    blocks_path: Path,
    *,
    char_limit: int | None = None,
) -> dict[str, str]:
    """Build snippets for top-level sections."""

    sections = json.loads(Path(sections_path).read_text(encoding="utf-8"))
    blocks_by_id = {block["id"]: block for block in _iter_blocks(blocks_path)}

    def _collect_texts(node: Mapping[str, Any]) -> list[str]:
        texts = [blocks_by_id.get(block_id, {}).get("text", "") for block_id in node.get("block_ids", [])]
        for child in node.get("children", []):
            texts.extend(_collect_texts(child))
        return texts

    snippets: dict[str, str] = {}
    for node in sections.get("root", {}).get("children", []):
        section_id = node.get("id")
        if not section_id:
            continue
        joined = " ".join(text for text in _collect_texts(node) if text)
        if char_limit is not None:
            joined = joined[:char_limit].rstrip()
        snippets[section_id] = joined
    return snippets


def load_style_summary(styles_path: Path) -> dict[str, Any]:
    """Return the JSON contents of ``styles.json`` unchanged."""

    return json.loads(Path(styles_path).read_text(encoding="utf-8"))


def write_debug_payload(out_dir: Path, payload: Mapping[str, Any]) -> None:
    """Write payload.debug.json with human-readable formatting."""

    debug_path = Path(out_dir) / "payload.debug.json"
    debug_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


TransportFn = Callable[..., Any]

_REAL_TRANSPORTS: dict[float, TransportFn] = {}


def _build_transport(temperature: float) -> TransportFn:
    """Construct a transport that may call the real API depending on configuration."""

    def _transport(
        *,
        system: str,
        payload: Mapping[str, Any],
        schema: Mapping[str, Any] | None,
    ) -> Any:
        if should_use_real_api():
            transport = _resolve_real_transport(temperature)
            return transport(system=system, payload=payload, schema=schema)

        _ = (system, schema)
        labels = [
            {
                "section_id": entry.get("section_id"),
                "role": "unsure",
                "topics": [],
            }
            for entry in payload.get("outline", [])
            if entry.get("section_id")
        ]
        response = {
            "doc_id": payload.get("doc_id", ""),
            "confidence": 0.0,
            "labels": labels,
        }
        return json.dumps(response)

    return _transport


def _resolve_real_transport(temperature: float) -> TransportFn:
    transport = _REAL_TRANSPORTS.get(temperature)
    if transport is None:
        transport = create_openai_transport(temperature=temperature)
        _REAL_TRANSPORTS[temperature] = transport
    return transport


def _run_batched_labeling(
    *,
    doc_id: str,
    outline_batches: list[list[dict[str, Any]]],
    snippets: Mapping[str, str],
    style_summary: Mapping[str, Any],
    transport: Any,
    schema: Mapping[str, Any] | None,
    section_lookup: set[str],
    payload_max_chars: int | None,
) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
    batch_results: list[tuple[dict[str, Any], dict[str, Any]]] = []
    batch_payloads: list[dict[str, Any]] = []

    for batch_outline in outline_batches:
        section_ids: list[str] = []
        for entry in batch_outline:
            section_id = entry.get("section_id")
            if isinstance(section_id, str) and section_id:
                section_ids.append(section_id)
        batch_snippets = _filter_snippets(snippets, section_ids)
        system_message, payload = build_labeling_prompt(
            doc_id,
            {
                "outline": batch_outline,
                "snippets": batch_snippets,
                "style_summary": style_summary,
            },
        )
        _ensure_payload_budget(payload, payload_max_chars)
        result, meta = run_labeling(
            system=system_message,
            payload=payload,
            transport=transport,
            schema=schema,
            section_lookup=section_lookup,
        )
        batch_results.append((result, meta))
        batch_payloads.append(payload)

    merged_result, merged_meta = _merge_batch_results(doc_id, batch_results)
    return merged_result, merged_meta, batch_payloads


def _split_outline(outline: list[dict[str, Any]], limit: int | None) -> list[list[dict[str, Any]]]:
    if not outline:
        return [outline]
    if limit is None or limit <= 0 or len(outline) <= limit:
        return [outline]
    return [outline[index : index + limit] for index in range(0, len(outline), limit)]


def _filter_snippets(snippets: Mapping[str, str], section_ids: list[str]) -> dict[str, str]:
    if not section_ids:
        return {}
    return {section_id: snippets.get(section_id, "") for section_id in section_ids}


def _merge_batch_results(
    doc_id: str,
    batch_results: Iterable[tuple[Mapping[str, Any], Mapping[str, Any]]],
) -> tuple[dict[str, Any], dict[str, Any]]:
    labels_by_section: OrderedDict[str, Mapping[str, Any]] = OrderedDict()
    confidence_min: float | None = None
    elapsed_total = 0.0
    usage_totals: dict[str, Any] = {}
    error_messages: list[str] = []
    resolved_doc_id = doc_id

    for result, meta in batch_results:
        result_doc_id = result.get("doc_id")
        if isinstance(result_doc_id, str) and result_doc_id:
            resolved_doc_id = result_doc_id

        confidence = result.get("confidence")
        if isinstance(confidence, (int, float)):
            confidence_value = float(confidence)
            confidence_min = confidence_value if confidence_min is None else min(confidence_min, confidence_value)

        for label in result.get("labels", []) or []:
            section_id = label.get("section_id")
            if section_id:
                labels_by_section[section_id] = label

        elapsed_total += float(meta.get("elapsed_sec") or 0.0)

        usage_meta = meta.get("usage")
        if isinstance(usage_meta, Mapping):
            usage_totals = _merge_usage_totals(usage_totals, usage_meta)

        error_messages.extend(_normalize_errors(meta.get("error")))

    merged_result = {
        "doc_id": resolved_doc_id,
        "confidence": confidence_min if confidence_min is not None else 0.0,
        "labels": list(labels_by_section.values()),
    }

    merged_meta: dict[str, Any] = {"elapsed_sec": elapsed_total}
    if usage_totals:
        merged_meta["usage"] = usage_totals
    if error_messages:
        merged_meta["error"] = error_messages
    return merged_result, merged_meta


def _merge_usage_totals(
    base: Mapping[str, Any],
    new_usage: Mapping[str, Any],
) -> dict[str, Any]:
    merged = dict(base)
    for key, value in new_usage.items():
        if isinstance(value, (int, float)):
            merged[key] = merged.get(key, 0) + value
        elif key not in merged:
            merged[key] = value
    return merged


def _ensure_payload_budget(payload: Mapping[str, Any], max_chars: int | None) -> None:
    if max_chars is None or max_chars <= 0:
        return
    payload_size = len(json.dumps(payload, ensure_ascii=False))
    if payload_size > max_chars:
        raise PayloadBudgetExceeded(payload_size, max_chars)


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _load_labels_schema() -> dict[str, Any]:
    return json.loads(LABELS_SCHEMA_PATH.read_text(encoding="utf-8"))


def _iter_blocks(blocks_path: Path) -> Iterator[Mapping[str, Any]]:
    yield from iter_jsonl(blocks_path)


def _iter_section_nodes(node: Mapping[str, Any]) -> Iterable[Mapping[str, Any]]:
    for child in node.get("children", []):
        yield child
        yield from _iter_section_nodes(child)


def _normalize_errors(raw: Any) -> list[str]:
    if not raw:
        return []
    if isinstance(raw, str):
        return [raw]
    if isinstance(raw, Mapping):
        return [str(value) for value in raw.values() if value]
    if isinstance(raw, Iterable) and not isinstance(raw, (str, bytes)):
        return [str(item) for item in raw if item]
    return [str(raw)]
