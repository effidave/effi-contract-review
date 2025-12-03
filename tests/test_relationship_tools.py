from __future__ import annotations

import json
from pathlib import Path

import pytest

from effilocal.mcp_server.tools.relationship_tools import (
    get_relationship_metadata,
)


@pytest.fixture
def analysis_dir_with_relationships(tmp_path: Path) -> Path:
    """Create a minimal analysis directory containing relationship artifacts."""

    manifest = {"doc_id": "test-doc", "attachments": []}
    (tmp_path / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    sections = {
        "root": {
            "children": [
                {
                    "id": "section-1",
                    "title": "Section 1",
                    "block_ids": ["block-1", "block-2"],
                    "children": [],
                }
            ]
        }
    }
    (tmp_path / "sections.json").write_text(json.dumps(sections), encoding="utf-8")

    styles = {"styles": []}
    (tmp_path / "styles.json").write_text(json.dumps(styles), encoding="utf-8")

    index = {"section_count": 1, "attachment_count": 0}
    (tmp_path / "index.json").write_text(json.dumps(index), encoding="utf-8")

    relationships = {
        "relationships": [
            {
                "block_id": "block-1",
                "parent_block_id": None,
                "child_block_ids": ["block-2"],
                "sibling_ordinal": 0,
                "restart_group_id": None,
                "list_meta": None,
                "clause_group_id": "block-1",
                "continuation_of": None,
                "attachment_id": None,
                "hierarchy_depth": 0,
            },
            {
                "block_id": "block-2",
                "parent_block_id": "block-1",
                "child_block_ids": [],
                "sibling_ordinal": 0,
                "restart_group_id": None,
                "list_meta": None,
                "clause_group_id": "block-2",
                "continuation_of": None,
                "attachment_id": None,
                "hierarchy_depth": 1,
            },
        ]
    }
    (tmp_path / "relationships.json").write_text(json.dumps(relationships), encoding="utf-8")

    blocks = [
        {
            "id": "block-1",
            "type": "heading",
            "text": "Heading 1",
            "para_id": "PARA001",
            "section_id": "section-1",
        },
        {
            "id": "block-2",
            "type": "paragraph",
            "text": "Paragraph 1",
            "para_id": "PARA002",
            "section_id": "section-1",
        },
    ]
    blocks_path = tmp_path / "blocks.jsonl"
    with blocks_path.open("w", encoding="utf-8") as handle:
        for entry in blocks:
            handle.write(json.dumps(entry))
            handle.write("\n")

    return tmp_path


def test_get_relationship_metadata_success(analysis_dir_with_relationships: Path) -> None:
    response = get_relationship_metadata(str(analysis_dir_with_relationships), "block-2")
    payload = json.loads(response)

    assert payload["success"] is True
    assert payload["block_id"] == "block-2"
    assert payload["parent_block"] == "block-1"
    assert payload["child_blocks"] == []
    assert payload["relationship"]["parent_block_id"] == "block-1"


def test_get_relationship_metadata_with_details(analysis_dir_with_relationships: Path) -> None:
    response = get_relationship_metadata(
        str(analysis_dir_with_relationships),
        "block-2",
        include_block_details=True,
    )
    payload = json.loads(response)

    assert payload["success"] is True
    assert isinstance(payload["parent_block"], dict)
    assert payload["parent_block"]["id"] == "block-1"
    assert isinstance(payload["child_blocks"], list)


def test_get_relationship_metadata_missing_block(analysis_dir_with_relationships: Path) -> None:
    response = get_relationship_metadata(str(analysis_dir_with_relationships), "missing")
    payload = json.loads(response)

    assert payload["success"] is False
    assert "not found" in payload["error"].lower()
