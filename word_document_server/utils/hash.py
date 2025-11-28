"""Helpers for computing repeatable SHA-256 checksums."""

from __future__ import annotations

import hashlib
from pathlib import Path

_CHUNK_SIZE = 8192


def sha256_file(path: Path) -> str:
    """Return the sha256 digest of a file as `sha256:<hex>`."""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(_CHUNK_SIZE), b""):
            digest.update(chunk)
    return f"sha256:{digest.hexdigest()}"


def norm_text_hash(text: str) -> str:
    """
    Normalize whitespace in ``text`` and return its sha256 digest.

    Normalization collapses all runs of whitespace into a single space and
    trims leading/trailing whitespace before hashing. The resulting digest is
    returned as ``sha256:<hex>``.
    """

    normalized = " ".join(text.split())
    digest = hashlib.sha256(normalized.encode("utf-8"))
    return f"sha256:{digest.hexdigest()}"
