"""Tests for artifact loader module."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from effilocal.artifact_loader import ArtifactLoader


@pytest.fixture
def sample_artifacts_dir(tmp_path: Path) -> Path:
    """Create sample artifact files for testing."""
    
    # manifest.json
    manifest = {
        "doc_id": "test-doc-123",
        "v": 1,
        "created_at": "2025-11-29T10:00:00+00:00",
        "checksums": {
            "raw.docx": "sha256:abc123",
            "blocks.jsonl": "sha256:def456",
        },
        "attachments": [
            {
                "attachment_id": "schedule-1",
                "type": "schedule",
                "label": "Schedule 1",
            }
        ],
    }
    (tmp_path / "manifest.json").write_text(json.dumps(manifest), encoding='utf-8')
    
    # blocks.jsonl
    blocks = [
        {
            "id": "block-1",
            "type": "list_item",
            "text": "This is clause 1.1",
            "para_id": "PARA001",
            "section_id": "section-1",
            "clause_group_id": "block-1",
            "list": {
                "ordinal": "1.1",
                "level": 0,
                "counters": [1, 1],
                "format": "decimal",
            },
        },
        {
            "id": "block-2",
            "type": "paragraph",
            "text": "Continuation of clause 1.1",
            "para_id": "PARA002",
            "section_id": "section-1",
            "clause_group_id": "block-1",
            "continuation_of": "block-1",
        },
        {
            "id": "block-3",
            "type": "list_item",
            "text": "This is clause 1.2",
            "para_id": "PARA003",
            "section_id": "section-1",
            "clause_group_id": "block-3",
            "list": {
                "ordinal": "1.2",
                "level": 0,
                "counters": [1, 2],
                "format": "decimal",
            },
        },
        {
            "id": "block-4",
            "type": "paragraph",
            "text": "Schedule content",
            "para_id": "PARA004",
            "section_id": "section-2",
            "clause_group_id": "block-4",
            "attachment_id": "schedule-1",
        },
    ]
    with open(tmp_path / "blocks.jsonl", "w", encoding='utf-8') as f:
        for block in blocks:
            f.write(json.dumps(block) + "\n")
    
    # sections.json
    sections = {
        "doc_id": "test-doc-123",
        "hierarchy_depth": 2,
        "root": {
            "children": [
                {
                    "id": "section-1",
                    "title": "Main Body",
                    "level": 1,
                    "block_ids": ["block-1", "block-2", "block-3"],
                    "children": [],
                },
                {
                    "id": "section-2",
                    "title": "Schedule 1",
                    "level": 1,
                    "block_ids": ["block-4"],
                    "attachment_id": "schedule-1",
                    "children": [],
                },
            ]
        },
    }
    (tmp_path / "sections.json").write_text(json.dumps(sections), encoding='utf-8')
    
    # relationships.json
    relationships = {
        "doc_id": "test-doc-123",
        "relationships": [
            {
                "block_id": "block-1",
                "parent_block_id": None,
                "child_block_ids": ["block-2"],
                "sibling_ordinal": 0,
            },
            {
                "block_id": "block-2",
                "parent_block_id": "block-1",
                "child_block_ids": [],
                "sibling_ordinal": 0,
            },
            {
                "block_id": "block-3",
                "parent_block_id": None,
                "child_block_ids": [],
                "sibling_ordinal": 1,
            },
            {
                "block_id": "block-4",
                "parent_block_id": None,
                "child_block_ids": [],
                "sibling_ordinal": 0,
            },
        ],
    }
    (tmp_path / "relationships.json").write_text(json.dumps(relationships), encoding='utf-8')
    
    # styles.json
    styles = {
        "doc_id": "test-doc-123",
        "styles": [
            {"style_id": "Normal", "style_name": "Normal", "count": 10},
        ],
    }
    (tmp_path / "styles.json").write_text(json.dumps(styles), encoding='utf-8')
    
    # index.json
    index = {
        "doc_id": "test-doc-123",
        "block_count": 4,
        "section_count": 2,
        "attachment_count": 1,
    }
    (tmp_path / "index.json").write_text(json.dumps(index), encoding='utf-8')
    
    return tmp_path


def test_loader_initialization(sample_artifacts_dir: Path):
    """Test basic loader initialization."""
    loader = ArtifactLoader(sample_artifacts_dir)
    
    assert loader.manifest['doc_id'] == 'test-doc-123'
    assert len(loader.blocks) == 4
    assert len(loader.blocks_by_id) == 4
    assert len(loader.sections_by_id) == 2


def test_missing_directory():
    """Test error handling for missing directory."""
    with pytest.raises(FileNotFoundError, match="Analysis directory not found"):
        ArtifactLoader("/nonexistent/path")


def test_missing_artifact_file(tmp_path: Path):
    """Test error handling for missing artifact files."""
    # Create directory but no files
    with pytest.raises(FileNotFoundError, match="Required artifact not found"):
        ArtifactLoader(tmp_path)


def test_find_clause_by_ordinal(sample_artifacts_dir: Path):
    """Test finding blocks by clause number."""
    loader = ArtifactLoader(sample_artifacts_dir)
    
    # Find existing clause
    clause = loader.find_clause_by_ordinal('1.1')
    assert clause is not None
    assert clause['id'] == 'block-1'
    assert clause['text'] == 'This is clause 1.1'
    
    # Find another clause
    clause = loader.find_clause_by_ordinal('1.2')
    assert clause is not None
    assert clause['id'] == 'block-3'
    
    # Non-existent clause
    clause = loader.find_clause_by_ordinal('99.99')
    assert clause is None


def test_find_block_by_para_id(sample_artifacts_dir: Path):
    """Test finding blocks by Word paragraph ID."""
    loader = ArtifactLoader(sample_artifacts_dir)
    
    block = loader.find_block_by_para_id('PARA001')
    assert block is not None
    assert block['id'] == 'block-1'
    
    block = loader.find_block_by_para_id('NONEXISTENT')
    assert block is None


def test_get_clause_group(sample_artifacts_dir: Path):
    """Test getting clause group (main + continuations)."""
    loader = ArtifactLoader(sample_artifacts_dir)
    
    # Get group for main clause
    group = loader.get_clause_group('block-1')
    assert len(group) == 2
    assert group[0]['id'] == 'block-1'
    assert group[1]['id'] == 'block-2'
    
    # Get group for continuation (should return same group)
    group = loader.get_clause_group('block-2')
    assert len(group) == 2
    
    # Clause without continuations
    group = loader.get_clause_group('block-3')
    assert len(group) == 1
    assert group[0]['id'] == 'block-3'
    
    # Non-existent block
    group = loader.get_clause_group('nonexistent')
    assert group == []


def test_get_section_blocks(sample_artifacts_dir: Path):
    """Test getting all blocks in a section."""
    loader = ArtifactLoader(sample_artifacts_dir)
    
    blocks = loader.get_section_blocks('section-1')
    assert len(blocks) == 3
    assert blocks[0]['id'] == 'block-1'
    assert blocks[1]['id'] == 'block-2'
    assert blocks[2]['id'] == 'block-3'
    
    blocks = loader.get_section_blocks('section-2')
    assert len(blocks) == 1
    assert blocks[0]['id'] == 'block-4'
    
    blocks = loader.get_section_blocks('nonexistent')
    assert blocks == []


def test_get_section_path(sample_artifacts_dir: Path):
    """Test getting breadcrumb path to section."""
    loader = ArtifactLoader(sample_artifacts_dir)
    
    path = loader.get_section_path('section-1')
    assert path == ['Main Body']
    
    path = loader.get_section_path('section-2')
    assert path == ['Schedule 1']
    
    path = loader.get_section_path('nonexistent')
    assert path == []


def test_get_schedules(sample_artifacts_dir: Path):
    """Test getting schedule metadata."""
    loader = ArtifactLoader(sample_artifacts_dir)
    
    schedules = loader.get_schedules()
    assert len(schedules) == 1
    assert schedules[0]['attachment_id'] == 'schedule-1'
    assert schedules[0]['label'] == 'Schedule 1'


def test_get_schedule_blocks(sample_artifacts_dir: Path):
    """Test getting blocks in a schedule."""
    loader = ArtifactLoader(sample_artifacts_dir)
    
    blocks = loader.get_schedule_blocks('schedule-1')
    assert len(blocks) == 1
    assert blocks[0]['id'] == 'block-4'
    assert blocks[0]['text'] == 'Schedule content'
    
    blocks = loader.get_schedule_blocks('nonexistent')
    assert blocks == []


def test_search_blocks_by_text(sample_artifacts_dir: Path):
    """Test searching blocks by text content."""
    loader = ArtifactLoader(sample_artifacts_dir)
    
    results = loader.search_blocks(text='clause 1.1')
    assert len(results) == 2  # Main clause + continuation
    
    results = loader.search_blocks(text='Schedule')
    assert len(results) == 1
    assert results[0]['id'] == 'block-4'
    
    results = loader.search_blocks(text='nonexistent')
    assert results == []


def test_search_blocks_by_type(sample_artifacts_dir: Path):
    """Test searching blocks by type."""
    loader = ArtifactLoader(sample_artifacts_dir)
    
    results = loader.search_blocks(block_type='list_item')
    assert len(results) == 2
    
    results = loader.search_blocks(block_type='paragraph')
    assert len(results) == 2


def test_search_blocks_by_numbering(sample_artifacts_dir: Path):
    """Test searching blocks by numbering presence."""
    loader = ArtifactLoader(sample_artifacts_dir)
    
    # Numbered blocks
    results = loader.search_blocks(has_numbering=True)
    assert len(results) == 2
    assert all(b.get('list') is not None for b in results)
    
    # Unnumbered blocks
    results = loader.search_blocks(has_numbering=False)
    assert len(results) == 2
    assert all(b.get('list') is None for b in results)


def test_search_blocks_combined(sample_artifacts_dir: Path):
    """Test searching with multiple filters."""
    loader = ArtifactLoader(sample_artifacts_dir)
    
    # Numbered list items containing "clause"
    results = loader.search_blocks(
        text='clause',
        block_type='list_item',
        has_numbering=True,
    )
    assert len(results) == 2


def test_get_relationship(sample_artifacts_dir: Path):
    """Test getting relationship metadata."""
    loader = ArtifactLoader(sample_artifacts_dir)
    
    rel = loader.get_relationship('block-1')
    assert rel is not None
    assert rel['parent_block_id'] is None
    assert rel['child_block_ids'] == ['block-2']
    
    rel = loader.get_relationship('block-2')
    assert rel is not None
    assert rel['parent_block_id'] == 'block-1'


def test_get_parent_block(sample_artifacts_dir: Path):
    """Test getting parent block in hierarchy."""
    loader = ArtifactLoader(sample_artifacts_dir)
    
    # Root block has no parent
    parent = loader.get_parent_block('block-1')
    assert parent is None
    
    # Child block has parent
    parent = loader.get_parent_block('block-2')
    assert parent is not None
    assert parent['id'] == 'block-1'


def test_get_child_blocks(sample_artifacts_dir: Path):
    """Test getting child blocks in hierarchy."""
    loader = ArtifactLoader(sample_artifacts_dir)
    
    # Block with children
    children = loader.get_child_blocks('block-1')
    assert len(children) == 1
    assert children[0]['id'] == 'block-2'
    
    # Block without children
    children = loader.get_child_blocks('block-2')
    assert children == []


def test_get_stats(sample_artifacts_dir: Path):
    """Test getting document statistics."""
    loader = ArtifactLoader(sample_artifacts_dir)
    
    stats = loader.get_stats()
    assert stats['doc_id'] == 'test-doc-123'
    assert stats['block_count'] == 4
    assert stats['section_count'] == 2
    assert stats['attachment_count'] == 1
    assert stats['numbered_blocks'] == 2
    assert stats['hierarchy_depth'] == 2
