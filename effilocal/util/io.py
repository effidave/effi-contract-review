"""Helpers for reading and writing newline-delimited JSON (JSONL)."""

from __future__ import annotations

import json
from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import Any

_LINE_ENDING = "\n"


def write_jsonl(path: Path, iterable_objs: Iterable[dict[str, Any]]) -> None:
    """
    Write dictionaries to a JSONL file using an atomic replace.

    A temporary file is written first to avoid leaving partially written
    artifacts if the process is interrupted.
    """

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")

    with tmp_path.open("w", encoding="utf-8", newline=_LINE_ENDING) as handle:
        for obj in iterable_objs:
            if not isinstance(obj, dict):
                raise TypeError(f"JSONL writer requires dict objects, got {type(obj)!r}")
            json.dump(obj, handle, ensure_ascii=False, separators=(",", ":"))
            handle.write(_LINE_ENDING)

    tmp_path.replace(path)


def iter_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    """Yield dictionaries from a JSONL file, ignoring blank lines."""

    path = Path(path)
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            loaded = json.loads(stripped)
            if not isinstance(loaded, dict):
                raise ValueError(
                    f"Line {line_number} in {path} did not deserialize to an object"
                )
            yield loaded
