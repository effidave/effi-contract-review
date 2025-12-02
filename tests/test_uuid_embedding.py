"""Tests for paragraph identification via native w14:paraId."""

from __future__ import annotations

import tempfile
from pathlib import Path
from uuid import uuid4

import pytest
from docx import Document
from docx.oxml.ns import qn

from effilocal.doc.uuid_embedding import (
    BlockKey,
    ParaKey,
    TableCellKey,
    extract_block_uuids,
    extract_block_para_ids,
    extract_block_uuids_legacy,
    get_paragraph_para_id,
    get_paragraph_uuid,
    find_paragraph_by_para_id,
    assign_block_ids,
    # Deprecated functions (should be no-ops)
    embed_block_uuids,
    remove_all_uuid_controls,
    remove_all_uuid_tags,
    set_paragraph_uuid,
)


def _add_para_id(para_elem, para_id: str):
    """Helper to add w14:paraId to a paragraph element."""
    para_elem.set(qn("w14:paraId"), para_id)


@pytest.fixture
def sample_doc() -> Document:
    """Create a sample document with paragraphs that have w14:paraId."""
    doc = Document()
    p1 = doc.add_paragraph("First paragraph")
    p2 = doc.add_paragraph("Second paragraph")
    p3 = doc.add_paragraph("Third paragraph")
    
    # Add w14:paraId to each paragraph (simulating what Word does)
    _add_para_id(p1._element, "00000001")
    _add_para_id(p2._element, "00000002")
    _add_para_id(p3._element, "00000003")
    
    return doc


@pytest.fixture
def sample_docx_path(sample_doc: Document) -> Path:
    """Save sample document to temp file and return path."""
    with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as f:
        sample_doc.save(f.name)
        return Path(f.name)


@pytest.fixture
def doc_with_table() -> Document:
    """Create a document with paragraphs and a table, all with w14:paraId."""
    doc = Document()
    
    intro = doc.add_paragraph("Intro paragraph")
    _add_para_id(intro._element, "0A0A0A01")
    
    # Add a 2x3 table
    table = doc.add_table(rows=2, cols=3)
    table.cell(0, 0).text = "Cell 0,0"
    table.cell(0, 1).text = "Cell 0,1"
    table.cell(0, 2).text = "Cell 0,2"
    table.cell(1, 0).text = "Cell 1,0"
    table.cell(1, 1).text = "Cell 1,1"
    table.cell(1, 2).text = "Cell 1,2"
    
    # Add w14:paraId to table cell paragraphs
    _add_para_id(table.cell(0, 0).paragraphs[0]._element, "0B0B0001")
    _add_para_id(table.cell(0, 1).paragraphs[0]._element, "0B0B0002")
    _add_para_id(table.cell(0, 2).paragraphs[0]._element, "0B0B0003")
    _add_para_id(table.cell(1, 0).paragraphs[0]._element, "0B0B0004")
    _add_para_id(table.cell(1, 1).paragraphs[0]._element, "0B0B0005")
    _add_para_id(table.cell(1, 2).paragraphs[0]._element, "0B0B0006")
    
    closing = doc.add_paragraph("Closing paragraph")
    _add_para_id(closing._element, "0A0A0A02")
    
    return doc


@pytest.fixture
def doc_with_table_path(doc_with_table: Document) -> Path:
    """Save document with table to temp file and return path."""
    with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as f:
        doc_with_table.save(f.name)
        return Path(f.name)


class TestGetParagraphParaId:
    """Tests for get_paragraph_para_id function."""

    def test_get_para_id(self, sample_doc: Document):
        """Test getting w14:paraId from a paragraph."""
        para = sample_doc.paragraphs[0]
        para_id = get_paragraph_para_id(para._element)
        assert para_id == "00000001"

    def test_backward_compat_alias(self, sample_doc: Document):
        """Test that get_paragraph_uuid is an alias for get_paragraph_para_id."""
        para = sample_doc.paragraphs[0]
        assert get_paragraph_uuid(para._element) == get_paragraph_para_id(para._element)

    def test_missing_para_id_returns_none(self):
        """Test that missing w14:paraId returns None."""
        doc = Document()
        para = doc.add_paragraph("No paraId")
        # Don't add w14:paraId
        
        para_id = get_paragraph_para_id(para._element)
        assert para_id is None


class TestFindParagraphByParaId:
    """Tests for find_paragraph_by_para_id function."""

    def test_find_body_paragraph(self, sample_doc: Document):
        """Test finding a body paragraph by w14:paraId."""
        para = find_paragraph_by_para_id(sample_doc, "00000002")
        assert para is not None
        assert para.text == "Second paragraph"

    def test_find_paragraph_case_insensitive(self, sample_doc: Document):
        """Test that search is case-insensitive."""
        # Search with lowercase
        para = find_paragraph_by_para_id(sample_doc, "00000002")
        assert para is not None
        
        # Original has uppercase
        _add_para_id(sample_doc.paragraphs[0]._element, "AABBCCDD")
        para = find_paragraph_by_para_id(sample_doc, "aabbccdd")
        assert para is not None

    def test_find_table_cell_paragraph(self, doc_with_table: Document):
        """Test finding a table cell paragraph by w14:paraId."""
        para = find_paragraph_by_para_id(doc_with_table, "0B0B0003")
        assert para is not None
        assert para.text == "Cell 0,2"

    def test_not_found_returns_none(self, sample_doc: Document):
        """Test that missing paraId returns None."""
        para = find_paragraph_by_para_id(sample_doc, "FFFFFFFF")
        assert para is None


class TestExtractBlockParaIds:
    """Tests for extract_block_para_ids function."""

    def test_extract_from_doc_object(self, sample_doc: Document):
        """Test extracting para_ids from Document object."""
        extracted = extract_block_para_ids(sample_doc)
        
        assert "00000001" in extracted
        assert "00000002" in extracted
        assert "00000003" in extracted
        
        assert extracted["00000001"] == ParaKey(0)
        assert extracted["00000002"] == ParaKey(1)
        assert extracted["00000003"] == ParaKey(2)

    def test_extract_from_path(self, sample_docx_path: Path):
        """Test extracting para_ids from file path."""
        extracted = extract_block_para_ids(sample_docx_path)
        
        assert len(extracted) == 3
        assert all(isinstance(k, str) for k in extracted.keys())
        assert all(isinstance(v, ParaKey) for v in extracted.values())

    def test_backward_compat_alias(self, sample_doc: Document):
        """Test that extract_block_uuids is an alias for extract_block_para_ids."""
        assert extract_block_uuids(sample_doc) == extract_block_para_ids(sample_doc)

    def test_extract_with_tables(self, doc_with_table: Document):
        """Test extracting para_ids including table cells."""
        extracted = extract_block_para_ids(doc_with_table)
        
        # Body paragraphs
        assert extracted.get("0A0A0A01") == ParaKey(0)
        assert extracted.get("0A0A0A02") == ParaKey(1)
        
        # Table cells
        assert extracted.get("0B0B0001") == TableCellKey(0, 0, 0)
        assert extracted.get("0B0B0002") == TableCellKey(0, 0, 1)
        assert extracted.get("0B0B0003") == TableCellKey(0, 0, 2)
        assert extracted.get("0B0B0004") == TableCellKey(0, 1, 0)
        assert extracted.get("0B0B0005") == TableCellKey(0, 1, 1)
        assert extracted.get("0B0B0006") == TableCellKey(0, 1, 2)

    def test_extract_empty_doc(self):
        """Test extracting from empty document."""
        doc = Document()
        extracted = extract_block_para_ids(doc)
        assert len(extracted) == 0


class TestExtractBlockUuidsLegacy:
    """Tests for extract_block_uuids_legacy function."""

    def test_returns_int_indices(self, sample_doc: Document):
        """Test that legacy function returns integer indices."""
        extracted = extract_block_uuids_legacy(sample_doc)
        
        assert extracted.get("00000001") == 0
        assert extracted.get("00000002") == 1
        assert extracted.get("00000003") == 2
        assert all(isinstance(v, int) for v in extracted.values())

    def test_only_body_paragraphs(self, doc_with_table: Document):
        """Test that legacy function only returns body paragraphs."""
        extracted = extract_block_uuids_legacy(doc_with_table)
        
        # Should only have body paragraphs
        assert "0A0A0A01" in extracted
        assert "0A0A0A02" in extracted
        
        # Should NOT have table cells
        assert "0B0B0001" not in extracted


class TestAssignBlockIds:
    """Tests for assign_block_ids function."""

    def test_assign_from_para_id(self):
        """Test assigning IDs based on para_id matching."""
        old_blocks = [
            {"id": "old-id-1", "para_id": "AAAA0001", "content_hash": "hash1"},
            {"id": "old-id-2", "para_id": "AAAA0002", "content_hash": "hash2"},
        ]
        new_blocks = [
            {"id": None, "para_id": "AAAA0001", "content_hash": "hash1-new"},
            {"id": None, "para_id": "AAAA0002", "content_hash": "hash2"},
        ]
        
        stats = assign_block_ids(new_blocks, old_blocks=old_blocks)
        
        assert new_blocks[0]["id"] == "old-id-1"
        assert new_blocks[1]["id"] == "old-id-2"
        assert stats["from_para_id"] == 2

    def test_assign_from_hash_fallback(self):
        """Test hash-based matching when para_id doesn't match."""
        old_blocks = [
            {"id": "old-id-1", "para_id": "AAAA0001", "content_hash": "same-hash"},
        ]
        new_blocks = [
            # Different para_id but same hash
            {"id": None, "para_id": "BBBB0001", "content_hash": "same-hash"},
        ]
        
        stats = assign_block_ids(new_blocks, old_blocks=old_blocks)
        
        assert new_blocks[0]["id"] == "old-id-1"
        assert stats["from_hash"] == 1

    def test_assign_from_position_fallback(self):
        """Test position-based matching as last resort."""
        old_blocks = [
            {"id": "old-id-1", "para_id": "AAAA0001", "para_idx": 0, 
             "type": "paragraph", "content_hash": "hash1"},
        ]
        new_blocks = [
            # Different para_id and hash, but nearby position and same type
            {"id": None, "para_id": "CCCC0001", "para_idx": 1, 
             "type": "paragraph", "content_hash": "hash-new"},
        ]
        
        stats = assign_block_ids(new_blocks, old_blocks=old_blocks, position_threshold=5)
        
        assert new_blocks[0]["id"] == "old-id-1"
        assert stats["from_position"] == 1

    def test_generate_new_id_from_para_id(self):
        """Test generating new ID using para_id when no match found."""
        new_blocks = [
            {"id": None, "para_id": "NEWPARA1", "content_hash": "new-hash"},
        ]
        
        stats = assign_block_ids(new_blocks, old_blocks=[])
        
        # Should use para_id as the new ID
        assert new_blocks[0]["id"] == "NEWPARA1"
        assert stats["generated"] == 1

    def test_skip_already_assigned(self):
        """Test that blocks with existing IDs are skipped."""
        new_blocks = [
            {"id": "existing-id", "para_id": "AAAA0001", "content_hash": "hash1"},
            {"id": None, "para_id": "AAAA0002", "content_hash": "hash2"},
        ]
        
        stats = assign_block_ids(new_blocks, old_blocks=[])
        
        assert new_blocks[0]["id"] == "existing-id"  # Unchanged
        assert new_blocks[1]["id"] == "AAAA0002"  # Assigned from para_id
        assert stats["generated"] == 1


class TestDeprecatedFunctions:
    """Tests for deprecated functions (should be no-ops)."""

    def test_embed_block_uuids_is_noop(self, sample_docx_path: Path):
        """Test that embed_block_uuids doesn't modify document."""
        # Get original file size/content
        original_size = sample_docx_path.stat().st_size
        
        blocks = [{"id": "test-id", "para_id": "00000001", "para_idx": 0}]
        result = embed_block_uuids(sample_docx_path, blocks)
        
        # Should return mapping but not modify document
        assert isinstance(result, dict)
        # File should be unchanged (deprecated function doesn't save)

    def test_set_paragraph_uuid_returns_true(self, sample_doc: Document):
        """Test that set_paragraph_uuid returns True (no-op)."""
        para = sample_doc.paragraphs[0]
        result = set_paragraph_uuid(sample_doc, para._element, "test-uuid")
        assert result is True

    def test_remove_all_uuid_tags_returns_zero(self, sample_docx_path: Path):
        """Test that remove_all_uuid_tags returns 0 (no-op)."""
        result = remove_all_uuid_tags(sample_docx_path)
        assert result == 0

    def test_remove_all_uuid_controls_alias(self, sample_docx_path: Path):
        """Test that remove_all_uuid_controls is alias for remove_all_uuid_tags."""
        result = remove_all_uuid_controls(sample_docx_path)
        assert result == 0


class TestTableCellParaIds:
    """Tests for w14:paraId in table cells."""

    def test_extract_table_cell_para_ids(self, doc_with_table_path: Path):
        """Test extracting para_ids from table cells."""
        extracted = extract_block_para_ids(doc_with_table_path)
        
        # Check table cell para_ids are extracted with correct keys
        assert extracted.get("0B0B0001") == TableCellKey(0, 0, 0)
        assert extracted.get("0B0B0006") == TableCellKey(0, 1, 2)

    def test_find_table_cell_by_para_id(self, doc_with_table: Document):
        """Test finding table cell paragraph by para_id."""
        para = find_paragraph_by_para_id(doc_with_table, "0B0B0004")
        assert para is not None
        assert para.text == "Cell 1,0"


class TestRealWorldDocument:
    """Tests with documents that have Word-assigned w14:paraId."""

    def test_extract_from_real_doc(self, tmp_path: Path):
        """Test extraction from a document saved and reloaded."""
        doc_path = tmp_path / "test.docx"
        
        # Create and save document
        doc = Document()
        p1 = doc.add_paragraph("Paragraph 1")
        p2 = doc.add_paragraph("Paragraph 2")
        
        # Simulate Word assigning paraIds
        _add_para_id(p1._element, "12345678")
        _add_para_id(p2._element, "ABCDEF00")
        
        doc.save(str(doc_path))
        
        # Reload and extract
        extracted = extract_block_para_ids(doc_path)
        
        assert "12345678" in extracted
        assert "ABCDEF00" in extracted

    def test_para_ids_survive_reload(self, tmp_path: Path):
        """Test that w14:paraId survives save/reload cycle."""
        doc_path = tmp_path / "test.docx"
        
        # Create document with paraIds
        doc = Document()
        p = doc.add_paragraph("Test")
        _add_para_id(p._element, "TESTID01")
        doc.save(str(doc_path))
        
        # Reload and check paraId still present
        doc2 = Document(str(doc_path))
        para_id = get_paragraph_para_id(doc2.paragraphs[0]._element)
        assert para_id == "TESTID01"
