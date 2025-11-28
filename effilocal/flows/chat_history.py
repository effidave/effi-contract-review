"""Conversation history persistence helpers for the chat CLI."""

from __future__ import annotations

import json
import os
from copy import deepcopy
from pathlib import Path
from typing import Any, Mapping, Sequence

CHAT_ARTIFACTS_ROOT = Path(os.environ.get("EFFILOCAL_CHAT_ARTIFACTS_DIR", "artifacts"))


class ConversationRecorder:
    """Collects per-run conversation entries for persistence."""

    def __init__(self) -> None:
        self.entries: list[dict[str, Any]] = []

    def record_user(self, content: str, *, metadata: Mapping[str, Any] | None = None) -> None:
        entry: dict[str, Any] = {
            "type": "message",
            "role": "user",
            "content": content,
        }
        if metadata:
            entry["metadata"] = dict(metadata)
        self.entries.append(entry)

    def record_assistant(self, content: str) -> None:
        self.entries.append(
            {
                "type": "message",
                "role": "assistant",
                "content": content,
            }
        )

    def record_tool_call(
        self,
        name: str,
        arguments: Mapping[str, Any],
        result: Mapping[str, Any],
    ) -> None:
        self.entries.append(
            {
                "type": "tool_call",
                "tool": name,
                "arguments": deepcopy(dict(arguments)),
                "result": deepcopy(dict(result)),
            }
        )


def _history_path(doc_id: str) -> Path:
    return CHAT_ARTIFACTS_ROOT / doc_id / "chat_history.jsonl"


def format_user_prompt(doc_id: str, question: str) -> str:
    """Render the user prompt content with the embedded document identifier."""

    stripped = (question or "").strip()
    return f"Document ID: {doc_id}\n\n{stripped}" if stripped else f"Document ID: {doc_id}"


def load_history_entries(doc_id: str) -> list[dict[str, Any]]:
    """Load stored history entries for ``doc_id``."""

    path = _history_path(doc_id)
    if not path.is_file():
        return []
    entries: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped:
                continue
            try:
                payload = json.loads(stripped)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict):
                entries.append(payload)
    return entries


def history_entries_to_messages(entries: Sequence[Mapping[str, Any]], doc_id: str) -> list[dict[str, Any]]:
    """Convert stored entries to chat messages for the next run."""

    messages: list[dict[str, Any]] = []
    for entry in entries:
        if entry.get("type") != "message":
            continue
        role = entry.get("role")
        if role not in {"user", "assistant"}:
            continue
        content = str(entry.get("content", "") or "")
        if role == "user":
            content = format_user_prompt(doc_id, content)
        message = {
            "role": role,
            "content": content,
        }
        messages.append(message)
    return messages


def append_history_entries(doc_id: str, entries: Sequence[Mapping[str, Any]]) -> None:
    """Append new conversation entries for ``doc_id``."""

    if not entries:
        return
    path = _history_path(doc_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        for entry in entries:
            handle.write(json.dumps(entry, ensure_ascii=False))
            handle.write("\n")


def clear_history(doc_id: str) -> None:
    """Delete the stored history for ``doc_id`` if it exists."""

    path = _history_path(doc_id)
    try:
        path.unlink()
    except FileNotFoundError:
        return
    parent = path.parent
    if parent.exists() and not any(parent.iterdir()):
        parent.rmdir()
