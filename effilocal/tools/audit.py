"""Audit logging utilities for tool dispatcher calls."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Mapping

AUDIT_FILE_ENV = "EFFILOCAL_TOOL_AUDIT_FILE"
DEFAULT_AUDIT_FILE = Path("tool_audit.jsonl")


def log_tool_call(
    *,
    tool: str,
    doc_id: str,
    args: Mapping[str, Any],
    truncated: bool,
    duration_ms: float,
) -> None:
    """Append a JSON line describing a tool call."""
    entry = {
        "tool": tool,
        "doc_id": doc_id,
        "args_digest": _digest_args(args),
        "duration_ms": round(duration_ms, 3),
        "truncated": bool(truncated),
    }
    path = _audit_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False))
        handle.write("\n")


def _audit_path() -> Path:
    override = os.getenv(AUDIT_FILE_ENV)
    return Path(override) if override else DEFAULT_AUDIT_FILE


def _digest_args(args: Mapping[str, Any]) -> str:
    payload = json.dumps(args, sort_keys=True, default=_stringify)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _stringify(value: Any) -> str:
    return str(value)
