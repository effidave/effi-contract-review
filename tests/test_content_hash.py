"""Tests for content hash and block matching."""

from __future__ import annotations

from uuid import uuid4

import pytest

from effilocal.doc.content_hash import (
    BlockMatch,
    MatchResult,
    compute_block_hash,
    match_blocks_by_hash,
)


class TestComputeBlockHash:
    """Tests for compute_block_hash function."""

    def test_basic_hash(self):
        """Test basic hash computation."""
        h = compute_block_hash("Hello World")
        assert h.startswith("sha256:")
        assert len(h) > 10

    def test_normalized_whitespace(self):
        """Test that whitespace is normalized."""
        h1 = compute_block_hash("Hello   World")
        h2 = compute_block_hash("Hello World")
        h3 = compute_block_hash("  Hello  World  ")
        
        assert h1 == h2
        assert h2 == h3

    def test_different_text_different_hash(self):
        """Test that different text produces different hashes."""
        h1 = compute_block_hash("Hello World")
        h2 = compute_block_hash("Goodbye World")
        
        assert h1 != h2

    def test_empty_string(self):
        """Test hash of empty string."""
        h = compute_block_hash("")
        assert h.startswith("sha256:")


class TestMatchResult:
    """Tests for MatchResult dataclass."""

    def test_method_counts(self):
        """Test counting matches by method."""
        matches = [
            BlockMatch("old1", "new1", "para_id", 1.0),
            BlockMatch("old2", "new2", "hash", 0.95),
            BlockMatch("old3", "new3", "hash", 0.9),
            BlockMatch("old4", "new4", "position", 0.6),
        ]
        result = MatchResult(matches=matches, unmatched_old=[], unmatched_new=[])
        
        assert result.matched_by_para_id == 1
        assert result.matched_by_hash == 2
        assert result.matched_by_position == 1

    def test_to_delta_dict(self):
        """Test conversion to delta dictionary."""
        matches = [
            BlockMatch("old1", "new1", "para_id", 1.0),
            BlockMatch("old2", "new2", "hash", 0.95),
        ]
        result = MatchResult(
            matches=matches,
            unmatched_old=["old3"],
            unmatched_new=["new3", "new4"],
        )
        
        delta = result.to_delta_dict()
        
        assert delta["matched_by_para_id"] == 1
        assert delta["matched_by_hash"] == 1
        assert delta["matched_by_position"] == 0
        assert delta["new_blocks"] == ["new3", "new4"]
        assert delta["deleted_blocks"] == ["old3"]


class TestMatchBlocksByHash:
    """Tests for match_blocks_by_hash function."""

    def test_empty_blocks(self):
        """Test matching empty block lists."""
        result = match_blocks_by_hash([], [])
        
        assert len(result.matches) == 0
        assert len(result.unmatched_old) == 0
        assert len(result.unmatched_new) == 0

    def test_identical_blocks(self):
        """Test matching identical block lists."""
        blocks = [
            {"id": "block-1", "text": "First paragraph", "para_idx": 0},
            {"id": "block-2", "text": "Second paragraph", "para_idx": 1},
        ]
        
        # Create new blocks with same content but different IDs
        new_blocks = [
            {"id": "new-1", "text": "First paragraph", "para_idx": 0},
            {"id": "new-2", "text": "Second paragraph", "para_idx": 1},
        ]
        
        result = match_blocks_by_hash(blocks, new_blocks)
        
        assert len(result.matches) == 2
        assert result.matched_by_hash == 2

    def test_para_id_matching_with_para_id_map(self):
        """Test para_id matching when para_id map is provided."""
        from effilocal.doc.uuid_embedding import ParaKey
        
        old_blocks = [
            {"id": "block-001", "text": "First paragraph", "para_idx": 0},
            {"id": "block-002", "text": "Second paragraph", "para_idx": 1},
        ]
        new_blocks = [
            {"id": "new-001", "text": "First paragraph", "para_idx": 0},
            {"id": "new-002", "text": "Second paragraph", "para_idx": 1},
        ]
        para_id_map = {
            "block-001": ParaKey(0),  # Para_id at para_idx 0
            "block-002": ParaKey(1),  # Para_id at para_idx 1
        }
        
        result = match_blocks_by_hash(
            old_blocks, 
            new_blocks,
            para_id_map=para_id_map,
        )
        
        assert result.matched_by_para_id == 2
        assert result.matched_by_hash == 0

    def test_para_id_matching_with_table_cells(self):
        """Test para_id matching for table cell blocks."""
        from effilocal.doc.uuid_embedding import ParaKey, TableCellKey
        
        old_blocks = [
            {"id": "block-para", "text": "Intro paragraph", "para_idx": 0},
            {"id": "block-cell-00", "text": "Cell 0,0", "table": {"table_id": "tbl_0", "row": 0, "col": 0}},
            {"id": "block-cell-11", "text": "Cell 1,1", "table": {"table_id": "tbl_0", "row": 1, "col": 1}},
        ]
        new_blocks = [
            {"id": "new-para", "text": "Intro paragraph", "para_idx": 0},
            {"id": "new-cell-00", "text": "Cell 0,0", "table": {"table_id": "tbl_0", "row": 0, "col": 0}},
            {"id": "new-cell-11", "text": "Cell 1,1", "table": {"table_id": "tbl_0", "row": 1, "col": 1}},
        ]
        para_id_map = {
            "block-para": ParaKey(0),
            "block-cell-00": TableCellKey(0, 0, 0),
            "block-cell-11": TableCellKey(0, 1, 1),
        }
        
        result = match_blocks_by_hash(
            old_blocks,
            new_blocks,
            para_id_map=para_id_map,
        )
        
        assert result.matched_by_para_id == 3
        assert result.matched_by_hash == 0
        assert len(result.unmatched_old) == 0
        assert len(result.unmatched_new) == 0

    def test_new_block_detection(self):
        """Test detection of new blocks."""
        old_blocks = [
            {"id": "old-1", "text": "First", "para_idx": 0},
        ]
        new_blocks = [
            {"id": "new-1", "text": "First", "para_idx": 0},
            {"id": "new-2", "text": "New paragraph", "para_idx": 1},
        ]
        
        result = match_blocks_by_hash(old_blocks, new_blocks)
        
        assert len(result.unmatched_new) == 1
        assert "new-2" in result.unmatched_new

    def test_deleted_block_detection(self):
        """Test detection of deleted blocks."""
        old_blocks = [
            {"id": "old-1", "text": "First", "para_idx": 0},
            {"id": "old-2", "text": "To be deleted", "para_idx": 1},
        ]
        new_blocks = [
            {"id": "new-1", "text": "First", "para_idx": 0},
        ]
        
        result = match_blocks_by_hash(old_blocks, new_blocks)
        
        assert len(result.unmatched_old) == 1
        assert "old-2" in result.unmatched_old

    def test_duplicate_hash_disambiguation(self):
        """Test disambiguation of blocks with same content hash."""
        old_blocks = [
            {"id": "old-1", "text": "Duplicate text", "para_idx": 0},
            {"id": "old-2", "text": "Duplicate text", "para_idx": 5},
        ]
        new_blocks = [
            {"id": "new-1", "text": "Duplicate text", "para_idx": 0},
            {"id": "new-2", "text": "Duplicate text", "para_idx": 5},
        ]
        
        result = match_blocks_by_hash(old_blocks, new_blocks)
        
        # Should match based on position proximity
        assert len(result.matches) == 2

    def test_modified_block_still_matches_by_hash(self):
        """Test that blocks with same content match even at different positions."""
        old_blocks = [
            {"id": "old-1", "text": "Unique content here", "para_idx": 0},
        ]
        new_blocks = [
            {"id": "new-1", "text": "Unique content here", "para_idx": 3},
        ]
        
        result = match_blocks_by_hash(old_blocks, new_blocks)
        
        assert len(result.matches) == 1
        assert result.matches[0].old_id == "old-1"
        assert result.matches[0].new_id == "new-1"


class TestPositionMatching:
    """Tests for position-based fallback matching."""

    def test_position_matching_for_unmatched(self):
        """Test that position matching is used for remaining unmatched blocks."""
        old_blocks = [
            {"id": "old-1", "text": "Content A modified", "para_idx": 0},
        ]
        new_blocks = [
            {"id": "new-1", "text": "Content A revised", "para_idx": 0},
        ]
        
        result = match_blocks_by_hash(old_blocks, new_blocks)
        
        # Content is different but position is same - should match by position
        # with lower confidence
        assert len(result.matches) == 1
        assert result.matches[0].method == "position"
        assert result.matches[0].confidence < 0.8

    def test_no_position_match_when_too_far(self):
        """Test that position matching fails for distant blocks."""
        old_blocks = [
            {"id": "old-1", "text": "Content A", "para_idx": 0},
        ]
        new_blocks = [
            {"id": "new-1", "text": "Different content", "para_idx": 20},
        ]
        
        result = match_blocks_by_hash(old_blocks, new_blocks)
        
        # Too far apart and different content - should not match
        assert len(result.unmatched_old) == 1
        assert len(result.unmatched_new) == 1
