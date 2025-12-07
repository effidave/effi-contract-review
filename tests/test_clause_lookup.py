#!/usr/bin/env python3
"""
Comprehensive tests for ClauseLookup class.

Tests verify:
- Loading blocks from list or Path
- Looking up clause number by para_id
- Looking up clause title by para_id (from heading.text or extracted from text)
- Looking up clause text by para_id
- Getting all clause info at once
- Handling missing para_ids gracefully
"""

import json
import sys
from pathlib import Path
from typing import Any

import pytest

# Add project root to path
_PROJECT_ROOT = Path(__file__).parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def sample_blocks() -> list[dict[str, Any]]:
    """Create sample blocks for testing."""
    return [
        {
            "id": "block-1",
            "para_id": "00000001",
            "text": "INDEMNIFICATION. The Vendor shall indemnify the Company...",
            "type": "list_item",
            "list": {
                "ordinal": "7.1",
                "level": 0,
                "format": "decimal"
            },
            "heading": {
                "text": "INDEMNIFICATION",
                "source": "explicit"
            }
        },
        {
            "id": "block-2",
            "para_id": "00000002",
            "text": "The indemnifying party shall defend any claims...",
            "type": "list_item",
            "list": {
                "ordinal": "7.2",
                "level": 0,
                "format": "decimal"
            },
            "heading": None
        },
        {
            "id": "block-3",
            "para_id": "00000003",
            "text": "Limitation of Liability. Neither party shall be liable...",
            "type": "list_item",
            "list": {
                "ordinal": "8.1",
                "level": 0,
                "format": "decimal"
            },
            "heading": None  # Title should be extracted from text
        },
        {
            "id": "block-4",
            "para_id": "00000004",
            "text": "This is a paragraph without numbering.",
            "type": "paragraph",
            "list": None,
            "heading": None
        },
        {
            "id": "block-5",
            "para_id": "00000005",
            "text": "Sub-clause content here.",
            "type": "list_item",
            "list": {
                "ordinal": "7.1(a)",
                "level": 1,
                "format": "lowerLetter"
            },
            "heading": None
        },
        {
            "id": "block-6",
            "para_id": "00000006",
            "text": "CONFIDENTIALITY AND NON-DISCLOSURE. Each party agrees...",
            "type": "list_item",
            "list": {
                "ordinal": "9",
                "level": 0,
                "format": "decimal"
            },
            "heading": None  # ALL CAPS title should be extracted
        },
    ]


@pytest.fixture
def blocks_jsonl_file(tmp_path: Path, sample_blocks: list[dict]) -> Path:
    """Create a temporary blocks.jsonl file."""
    blocks_file = tmp_path / "blocks.jsonl"
    with open(blocks_file, "w", encoding="utf-8") as f:
        for block in sample_blocks:
            f.write(json.dumps(block) + "\n")
    return blocks_file


# =============================================================================
# Tests for ClauseLookup initialization
# =============================================================================

class TestClauseLookupInit:
    """Tests for ClauseLookup initialization from different sources."""
    
    def test_init_from_blocks_list(self, sample_blocks: list[dict]) -> None:
        """Should initialize from a list of block dictionaries."""
        from effilocal.doc.clause_lookup import ClauseLookup
        
        lookup = ClauseLookup(sample_blocks)
        
        assert lookup is not None
        assert len(lookup._blocks_by_para_id) == 6
    
    def test_init_from_path(self, blocks_jsonl_file: Path) -> None:
        """Should initialize from a Path to blocks.jsonl."""
        from effilocal.doc.clause_lookup import ClauseLookup
        
        lookup = ClauseLookup(blocks_jsonl_file)
        
        assert lookup is not None
        assert len(lookup._blocks_by_para_id) == 6
    
    def test_init_from_empty_list(self) -> None:
        """Should handle empty blocks list gracefully."""
        from effilocal.doc.clause_lookup import ClauseLookup
        
        lookup = ClauseLookup([])
        
        assert lookup is not None
        assert len(lookup._blocks_by_para_id) == 0
    
    def test_init_from_nonexistent_path_raises(self, tmp_path: Path) -> None:
        """Should raise FileNotFoundError for nonexistent path."""
        from effilocal.doc.clause_lookup import ClauseLookup
        
        with pytest.raises(FileNotFoundError):
            ClauseLookup(tmp_path / "nonexistent.jsonl")
    
    def test_init_builds_para_id_index(self, sample_blocks: list[dict]) -> None:
        """Should build index keyed by para_id."""
        from effilocal.doc.clause_lookup import ClauseLookup
        
        lookup = ClauseLookup(sample_blocks)
        
        # Check specific para_ids are indexed
        assert "00000001" in lookup._blocks_by_para_id
        assert "00000002" in lookup._blocks_by_para_id
        assert "00000003" in lookup._blocks_by_para_id


# =============================================================================
# Tests for get_clause_number
# =============================================================================

class TestGetClauseNumber:
    """Tests for looking up clause number by para_id."""
    
    def test_returns_ordinal_for_numbered_clause(self, sample_blocks: list[dict]) -> None:
        """Should return list.ordinal for numbered clauses."""
        from effilocal.doc.clause_lookup import ClauseLookup
        
        lookup = ClauseLookup(sample_blocks)
        
        assert lookup.get_clause_number("00000001") == "7.1"
        assert lookup.get_clause_number("00000002") == "7.2"
        assert lookup.get_clause_number("00000003") == "8.1"
    
    def test_returns_sub_clause_ordinal(self, sample_blocks: list[dict]) -> None:
        """Should return full ordinal for sub-clauses like 7.1(a)."""
        from effilocal.doc.clause_lookup import ClauseLookup
        
        lookup = ClauseLookup(sample_blocks)
        
        assert lookup.get_clause_number("00000005") == "7.1(a)"
    
    def test_returns_none_for_unnumbered_paragraph(self, sample_blocks: list[dict]) -> None:
        """Should return None for paragraphs without list info."""
        from effilocal.doc.clause_lookup import ClauseLookup
        
        lookup = ClauseLookup(sample_blocks)
        
        assert lookup.get_clause_number("00000004") is None
    
    def test_returns_none_for_unknown_para_id(self, sample_blocks: list[dict]) -> None:
        """Should return None for para_ids not in the index."""
        from effilocal.doc.clause_lookup import ClauseLookup
        
        lookup = ClauseLookup(sample_blocks)
        
        assert lookup.get_clause_number("UNKNOWN") is None
        assert lookup.get_clause_number("") is None
    
    def test_strips_trailing_period_from_ordinal(self) -> None:
        """Should strip trailing periods from ordinals for cleaner display."""
        from effilocal.doc.clause_lookup import ClauseLookup
        
        blocks = [{
            "id": "block-1",
            "para_id": "ABC123",
            "text": "Some text",
            "list": {"ordinal": "1.2.", "level": 0}
        }]
        
        lookup = ClauseLookup(blocks)
        
        # Ordinal should be cleaned
        assert lookup.get_clause_number("ABC123") == "1.2"


# =============================================================================
# Tests for get_clause_title
# =============================================================================

class TestGetClauseTitle:
    """Tests for looking up clause title by para_id."""
    
    def test_returns_heading_text_when_present(self, sample_blocks: list[dict]) -> None:
        """Should return heading.text when block has explicit heading."""
        from effilocal.doc.clause_lookup import ClauseLookup
        
        lookup = ClauseLookup(sample_blocks)
        
        assert lookup.get_clause_title("00000001") == "INDEMNIFICATION"
    
    def test_extracts_title_case_title_from_text(self, sample_blocks: list[dict]) -> None:
        """Should extract Title Case title from paragraph text."""
        from effilocal.doc.clause_lookup import ClauseLookup
        
        lookup = ClauseLookup(sample_blocks)
        
        # Block 3: "Limitation of Liability. Neither party shall..."
        assert lookup.get_clause_title("00000003") == "Limitation of Liability"
    
    def test_extracts_all_caps_title_from_text(self, sample_blocks: list[dict]) -> None:
        """Should extract ALL CAPS title from paragraph text."""
        from effilocal.doc.clause_lookup import ClauseLookup
        
        lookup = ClauseLookup(sample_blocks)
        
        # Block 6: "CONFIDENTIALITY AND NON-DISCLOSURE. Each party..."
        assert lookup.get_clause_title("00000006") == "CONFIDENTIALITY AND NON-DISCLOSURE"
    
    def test_returns_none_when_no_title(self, sample_blocks: list[dict]) -> None:
        """Should return None when no title can be determined."""
        from effilocal.doc.clause_lookup import ClauseLookup
        
        lookup = ClauseLookup(sample_blocks)
        
        # Block 2: "The indemnifying party shall defend..." - no title pattern
        assert lookup.get_clause_title("00000002") is None
        
        # Block 4: "This is a paragraph without numbering." - no title
        assert lookup.get_clause_title("00000004") is None
    
    def test_returns_none_for_unknown_para_id(self, sample_blocks: list[dict]) -> None:
        """Should return None for unknown para_ids."""
        from effilocal.doc.clause_lookup import ClauseLookup
        
        lookup = ClauseLookup(sample_blocks)
        
        assert lookup.get_clause_title("UNKNOWN") is None
    
    def test_prefers_heading_over_extracted_title(self) -> None:
        """When block has both heading.text and extractable title, prefer heading."""
        from effilocal.doc.clause_lookup import ClauseLookup
        
        blocks = [{
            "id": "block-1",
            "para_id": "ABC123",
            "text": "DIFFERENT TITLE. Some content here.",
            "heading": {"text": "Preferred Heading", "source": "explicit"}
        }]
        
        lookup = ClauseLookup(blocks)
        
        assert lookup.get_clause_title("ABC123") == "Preferred Heading"


# =============================================================================
# Tests for get_clause_text
# =============================================================================

class TestGetClauseText:
    """Tests for looking up clause text by para_id."""
    
    def test_returns_block_text(self, sample_blocks: list[dict]) -> None:
        """Should return the block's text field."""
        from effilocal.doc.clause_lookup import ClauseLookup
        
        lookup = ClauseLookup(sample_blocks)
        
        text = lookup.get_clause_text("00000001")
        assert text == "INDEMNIFICATION. The Vendor shall indemnify the Company..."
    
    def test_returns_text_for_unnumbered_paragraph(self, sample_blocks: list[dict]) -> None:
        """Should return text even for unnumbered paragraphs."""
        from effilocal.doc.clause_lookup import ClauseLookup
        
        lookup = ClauseLookup(sample_blocks)
        
        assert lookup.get_clause_text("00000004") == "This is a paragraph without numbering."
    
    def test_returns_none_for_unknown_para_id(self, sample_blocks: list[dict]) -> None:
        """Should return None for unknown para_ids."""
        from effilocal.doc.clause_lookup import ClauseLookup
        
        lookup = ClauseLookup(sample_blocks)
        
        assert lookup.get_clause_text("UNKNOWN") is None


# =============================================================================
# Tests for get_clause_info
# =============================================================================

class TestGetClauseInfo:
    """Tests for getting all clause info at once."""
    
    def test_returns_dict_with_all_fields(self, sample_blocks: list[dict]) -> None:
        """Should return dict with clause_number, clause_title, and text."""
        from effilocal.doc.clause_lookup import ClauseLookup
        
        lookup = ClauseLookup(sample_blocks)
        
        info = lookup.get_clause_info("00000001")
        
        assert info is not None
        assert info["clause_number"] == "7.1"
        assert info["clause_title"] == "INDEMNIFICATION"
        assert "The Vendor shall indemnify" in info["text"]
    
    def test_returns_none_values_for_missing_data(self, sample_blocks: list[dict]) -> None:
        """Should return None for fields that don't exist."""
        from effilocal.doc.clause_lookup import ClauseLookup
        
        lookup = ClauseLookup(sample_blocks)
        
        # Block 4 has no numbering and no title
        info = lookup.get_clause_info("00000004")
        
        assert info is not None
        assert info["clause_number"] is None
        assert info["clause_title"] is None
        assert info["text"] == "This is a paragraph without numbering."
    
    def test_returns_none_for_unknown_para_id(self, sample_blocks: list[dict]) -> None:
        """Should return None for unknown para_ids."""
        from effilocal.doc.clause_lookup import ClauseLookup
        
        lookup = ClauseLookup(sample_blocks)
        
        assert lookup.get_clause_info("UNKNOWN") is None
    
    def test_info_includes_para_id(self, sample_blocks: list[dict]) -> None:
        """Returned info should include the para_id for reference."""
        from effilocal.doc.clause_lookup import ClauseLookup
        
        lookup = ClauseLookup(sample_blocks)
        
        info = lookup.get_clause_info("00000001")
        
        assert info["para_id"] == "00000001"


# =============================================================================
# Tests for extract_clause_title_from_text helper
# =============================================================================

class TestExtractClauseTitleFromText:
    """Tests for the title extraction helper function."""
    
    def test_extracts_all_caps_title(self) -> None:
        """Should extract ALL CAPS title ending with period."""
        from effilocal.doc.clause_lookup import extract_clause_title_from_text
        
        assert extract_clause_title_from_text("INDEMNIFICATION. The Vendor...") == "INDEMNIFICATION"
        assert extract_clause_title_from_text("LIMITATION OF LIABILITY. Neither party...") == "LIMITATION OF LIABILITY"
    
    def test_extracts_title_case_title(self) -> None:
        """Should extract Title Case title ending with period."""
        from effilocal.doc.clause_lookup import extract_clause_title_from_text
        
        assert extract_clause_title_from_text("Indemnification. The Vendor...") == "Indemnification"
        assert extract_clause_title_from_text("Limitation of Liability. Neither party...") == "Limitation of Liability"
    
    def test_handles_special_characters_in_title(self) -> None:
        """Should handle &, commas, hyphens in ALL CAPS titles."""
        from effilocal.doc.clause_lookup import extract_clause_title_from_text
        
        assert extract_clause_title_from_text("TERMS & CONDITIONS. The following...") == "TERMS & CONDITIONS"
        assert extract_clause_title_from_text("NON-DISCLOSURE. Each party...") == "NON-DISCLOSURE"
    
    def test_returns_empty_for_no_title(self) -> None:
        """Should return empty string when no title pattern found."""
        from effilocal.doc.clause_lookup import extract_clause_title_from_text
        
        assert extract_clause_title_from_text("The Vendor shall provide services.") == ""
        assert extract_clause_title_from_text("") == ""
        assert extract_clause_title_from_text("lowercase title. Some content.") == ""
    
    def test_rejects_short_titles(self) -> None:
        """Should reject titles that are too short (less than 3 chars)."""
        from effilocal.doc.clause_lookup import extract_clause_title_from_text
        
        assert extract_clause_title_from_text("AB. Not a title.") == ""
    
    def test_rejects_long_title_case_titles(self) -> None:
        """Should reject Title Case titles longer than 50 chars."""
        from effilocal.doc.clause_lookup import extract_clause_title_from_text
        
        long_title = "A Very Long Title That Exceeds The Maximum Allowed Length For Title Case. Content..."
        assert extract_clause_title_from_text(long_title) == ""


# =============================================================================
# Tests for edge cases
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases and error handling."""
    
    def test_handles_blocks_without_para_id(self) -> None:
        """Should skip blocks that don't have para_id."""
        from effilocal.doc.clause_lookup import ClauseLookup
        
        blocks = [
            {"id": "block-1", "text": "No para_id here"},
            {"id": "block-2", "para_id": "ABC123", "text": "Has para_id"}
        ]
        
        lookup = ClauseLookup(blocks)
        
        assert len(lookup._blocks_by_para_id) == 1
        assert "ABC123" in lookup._blocks_by_para_id
    
    def test_handles_blocks_with_empty_para_id(self) -> None:
        """Should skip blocks with empty para_id."""
        from effilocal.doc.clause_lookup import ClauseLookup
        
        blocks = [
            {"id": "block-1", "para_id": "", "text": "Empty para_id"},
            {"id": "block-2", "para_id": "ABC123", "text": "Has para_id"}
        ]
        
        lookup = ClauseLookup(blocks)
        
        assert len(lookup._blocks_by_para_id) == 1
    
    def test_handles_malformed_list_info(self) -> None:
        """Should handle blocks with malformed list info gracefully."""
        from effilocal.doc.clause_lookup import ClauseLookup
        
        blocks = [
            {"id": "block-1", "para_id": "ABC123", "text": "Text", "list": {}},
            {"id": "block-2", "para_id": "DEF456", "text": "Text", "list": {"level": 0}},  # No ordinal
        ]
        
        lookup = ClauseLookup(blocks)
        
        assert lookup.get_clause_number("ABC123") is None
        assert lookup.get_clause_number("DEF456") is None
    
    def test_duplicate_para_ids_last_wins(self) -> None:
        """If duplicate para_ids exist, last one should win."""
        from effilocal.doc.clause_lookup import ClauseLookup
        
        blocks = [
            {"id": "block-1", "para_id": "ABC123", "text": "First"},
            {"id": "block-2", "para_id": "ABC123", "text": "Second"}
        ]
        
        lookup = ClauseLookup(blocks)
        
        assert lookup.get_clause_text("ABC123") == "Second"
