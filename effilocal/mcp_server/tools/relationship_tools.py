"""Tools for surfacing block relationship metadata from analysis artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from effilocal.artifact_loader import ArtifactLoader


def _coerce_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        return normalized in {"1", "true", "yes", "y", "on"}
    return bool(value)


def get_relationship_metadata(
    analysis_dir: str,
    block_id: str,
    include_block_details: bool = False,
) -> str:
    """Return relationship metadata for a block from an analysis directory."""

    if not analysis_dir or not str(analysis_dir).strip():
        return json.dumps(
            {
                "success": False,
                "error": "analysis_dir is required.",
            },
            indent=2,
        )

    if not block_id or not str(block_id).strip():
        return json.dumps(
            {
                "success": False,
                "error": "block_id is required.",
            },
            indent=2,
        )

    analysis_path = Path(analysis_dir).expanduser()

    if not analysis_path.exists():
        return json.dumps(
            {
                "success": False,
                "error": f"Analysis directory not found: {analysis_path}",
            },
            indent=2,
        )

    if not analysis_path.is_dir():
        return json.dumps(
            {
                "success": False,
                "error": f"analysis_dir must be a directory: {analysis_path}",
            },
            indent=2,
        )

    try:
        loader = ArtifactLoader(analysis_path)
    except FileNotFoundError as exc:
        return json.dumps(
            {
                "success": False,
                "error": f"Missing artifact file: {exc}",
            },
            indent=2,
        )
    except json.JSONDecodeError as exc:
        return json.dumps(
            {
                "success": False,
                "error": f"Malformed artifact JSON: {exc}",
            },
            indent=2,
        )
    except Exception as exc:  # pragma: no cover - defensive
        return json.dumps(
            {
                "success": False,
                "error": f"Failed to load artifacts: {exc}",
            },
            indent=2,
        )

    relationship = loader.get_relationship(block_id)
    if relationship is None:
        return json.dumps(
            {
                "success": False,
                "error": f"Relationship not found for block_id: {block_id}",
            },
            indent=2,
        )

    include_details = _coerce_bool(include_block_details)

    parent_block = loader.get_parent_block(block_id)
    child_blocks = loader.get_child_blocks(block_id)

    if include_details:
        parent_payload: Any = parent_block
        child_payload: Any = child_blocks
    else:
        parent_payload = parent_block["id"] if parent_block else None
        child_payload = [child["id"] for child in child_blocks] if child_blocks else []

    payload = {
        "success": True,
        "analysis_dir": str(analysis_path.resolve()),
        "block_id": block_id,
        "relationship": relationship,
        "parent_block": parent_payload,
        "child_blocks": child_payload,
    }

    return json.dumps(payload, indent=2)
