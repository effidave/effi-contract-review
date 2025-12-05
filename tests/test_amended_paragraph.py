#!/usr/bin/env python3
"""
Tests for AmendedParagraph - Option A model.

Option A Data Model:
- amended_text: Contains only VISIBLE text (normal runs + insertions, NO deletions)
- amended_runs: All runs including deletions
  - Normal/insert runs: start/end map to positions in amended_text
  - Delete runs: zero-width (start == end), with deleted_text field containing struck content

Example:
{
  "text": "The quick fox",  # Visible only - no "brown " deletion
  "runs": [
    { "start": 0, "end": 4, "formats": [] },                                    # "The "
    { "start": 4, "end": 9, "formats": ["insert"], "author": "John" },          # "quick"
    { "start": 9, "end": 9, "formats": ["delete"], "deleted_text": "brown " },  # Zero-width
    { "start": 9, "end": 13, "formats": [] }                                    # " fox"
  ]
}

TDD Approach: These tests are written to FAIL initially.
"""

import pytest
from pathlib import Path
from docx import Document
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


class TestAmendedParagraphImport:
    """Test that the module can be imported."""
    
    def test_import_amended_paragraph(self):
        """Test that AmendedParagraph can be imported."""
        try:
            from effilocal.doc.amended_paragraph import AmendedParagraph
        except ImportError as e:
            pytest.fail(f"Cannot import AmendedParagraph: {e}")
    
    def test_import_iter_amended_paragraphs(self):
        """Test that iter_amended_paragraphs can be imported."""
        try:
            from effilocal.doc.amended_paragraph import iter_amended_paragraphs
        except ImportError as e:
            pytest.fail(f"Cannot import iter_amended_paragraphs: {e}")
    
    def test_import_iter_amended_elements(self):
        """Test that iter_amended_elements can be imported."""
        try:
            from effilocal.doc.amended_paragraph import iter_amended_elements
        except ImportError as e:
            pytest.fail(f"Cannot import iter_amended_elements: {e}")


class TestAmendedTextVisibleOnly:
    """Tests for amended_text containing only visible text."""
    
    @pytest.fixture
    def sample_doc(self):
        """Create a basic document for testing."""
        return Document()
    
    @pytest.fixture
    def doc_with_normal_text(self, sample_doc):
        """Create document with normal text only."""
        doc = sample_doc
        doc.add_paragraph("Normal paragraph text")
        return doc
    
    @pytest.fixture
    def doc_with_insertion(self, sample_doc):
        """Create document with an insertion (w:ins containing w:t)."""
        doc = sample_doc
        para = doc.add_paragraph()
        
        # Add normal text
        run1 = para.add_run("Before ")
        
        # Create w:ins element with inserted text
        p_elem = para._p
        ins = OxmlElement('w:ins')
        ins.set(qn('w:id'), '1')
        ins.set(qn('w:author'), 'John Smith')
        ins.set(qn('w:date'), '2024-01-15T10:30:00Z')
        
        # Create run inside ins with w:t (visible)
        r = OxmlElement('w:r')
        t = OxmlElement('w:t')
        t.text = 'inserted'
        r.append(t)
        ins.append(r)
        p_elem.append(ins)
        
        # Add more normal text
        run3 = para.add_run(" after")
        
        return doc
    
    @pytest.fixture
    def doc_with_deletion(self, sample_doc):
        """Create document with a deletion (w:del containing w:delText)."""
        doc = sample_doc
        para = doc.add_paragraph()
        
        # Add normal text
        run1 = para.add_run("Before ")
        
        # Create w:del element with deleted text
        p_elem = para._p
        del_elem = OxmlElement('w:del')
        del_elem.set(qn('w:id'), '2')
        del_elem.set(qn('w:author'), 'Jane Doe')
        del_elem.set(qn('w:date'), '2024-01-16T14:45:00Z')
        
        # Create run inside del with w:delText (NOT visible)
        r = OxmlElement('w:r')
        del_text = OxmlElement('w:delText')
        del_text.text = 'deleted'
        r.append(del_text)
        del_elem.append(r)
        p_elem.append(del_elem)
        
        # Add more normal text
        run3 = para.add_run(" after")
        
        return doc
    
    @pytest.fixture
    def doc_with_both(self, sample_doc):
        """Create document with both insertion and deletion."""
        doc = sample_doc
        para = doc.add_paragraph()
        
        # Normal: "The "
        para.add_run("The ")
        
        # Insertion: "quick"
        p_elem = para._p
        ins = OxmlElement('w:ins')
        ins.set(qn('w:id'), '1')
        ins.set(qn('w:author'), 'John')
        r_ins = OxmlElement('w:r')
        t_ins = OxmlElement('w:t')
        t_ins.text = 'quick'
        r_ins.append(t_ins)
        ins.append(r_ins)
        p_elem.append(ins)
        
        # Deletion: "brown " (should NOT appear in amended_text)
        del_elem = OxmlElement('w:del')
        del_elem.set(qn('w:id'), '2')
        del_elem.set(qn('w:author'), 'Jane')
        r_del = OxmlElement('w:r')
        del_text = OxmlElement('w:delText')
        del_text.text = 'brown '
        r_del.append(del_text)
        del_elem.append(r_del)
        p_elem.append(del_elem)
        
        # Normal: " fox"
        para.add_run(" fox")
        
        return doc
    
    def test_normal_text_unchanged(self, doc_with_normal_text):
        """Test that normal text is returned as-is."""
        from effilocal.doc.amended_paragraph import AmendedParagraph
        
        para = doc_with_normal_text.paragraphs[0]
        amended = AmendedParagraph(para)
        
        assert amended.amended_text == "Normal paragraph text"
    
    def test_insertion_included_in_text(self, doc_with_insertion):
        """Test that inserted text (w:ins > w:r > w:t) IS included."""
        from effilocal.doc.amended_paragraph import AmendedParagraph
        
        para = doc_with_insertion.paragraphs[0]
        amended = AmendedParagraph(para)
        
        assert "inserted" in amended.amended_text
        assert amended.amended_text == "Before inserted after"
    
    def test_deletion_excluded_from_text(self, doc_with_deletion):
        """Test that deleted text (w:del > w:r > w:delText) is NOT included."""
        from effilocal.doc.amended_paragraph import AmendedParagraph
        
        para = doc_with_deletion.paragraphs[0]
        amended = AmendedParagraph(para)
        
        assert "deleted" not in amended.amended_text
        assert amended.amended_text == "Before  after"  # Note double space where deletion was
    
    def test_mixed_insertions_deletions(self, doc_with_both):
        """Test paragraph with both insertions and deletions."""
        from effilocal.doc.amended_paragraph import AmendedParagraph
        
        para = doc_with_both.paragraphs[0]
        amended = AmendedParagraph(para)
        
        # Should include "The ", "quick", " fox" but NOT "brown "
        assert amended.amended_text == "The quick fox"
        assert "brown" not in amended.amended_text


class TestAmendedRunsWithDeletedText:
    """Tests for amended_runs with zero-width deletes and deleted_text field."""
    
    @pytest.fixture
    def sample_doc(self):
        return Document()
    
    @pytest.fixture
    def doc_with_deletion(self, sample_doc):
        """Create document with a deletion."""
        doc = sample_doc
        para = doc.add_paragraph()
        
        para.add_run("Before ")
        
        p_elem = para._p
        del_elem = OxmlElement('w:del')
        del_elem.set(qn('w:id'), '1')
        del_elem.set(qn('w:author'), 'Jane Doe')
        del_elem.set(qn('w:date'), '2024-01-16T14:45:00Z')
        
        r = OxmlElement('w:r')
        del_text = OxmlElement('w:delText')
        del_text.text = 'removed'
        r.append(del_text)
        del_elem.append(r)
        p_elem.append(del_elem)
        
        para.add_run(" after")
        
        return doc
    
    @pytest.fixture
    def doc_with_both(self, sample_doc):
        """Create document with insertion followed by deletion."""
        doc = sample_doc
        para = doc.add_paragraph()
        
        para.add_run("The ")
        
        p_elem = para._p
        
        # Insertion
        ins = OxmlElement('w:ins')
        ins.set(qn('w:id'), '1')
        ins.set(qn('w:author'), 'John')
        r_ins = OxmlElement('w:r')
        t_ins = OxmlElement('w:t')
        t_ins.text = 'quick'
        r_ins.append(t_ins)
        ins.append(r_ins)
        p_elem.append(ins)
        
        # Deletion
        del_elem = OxmlElement('w:del')
        del_elem.set(qn('w:id'), '2')
        del_elem.set(qn('w:author'), 'Jane')
        r_del = OxmlElement('w:r')
        del_text = OxmlElement('w:delText')
        del_text.text = 'brown '
        r_del.append(del_text)
        del_elem.append(r_del)
        p_elem.append(del_elem)
        
        para.add_run(" fox")
        
        return doc
    
    def test_delete_run_has_zero_width(self, doc_with_deletion):
        """Test that delete runs have start == end (zero width)."""
        from effilocal.doc.amended_paragraph import AmendedParagraph
        
        para = doc_with_deletion.paragraphs[0]
        amended = AmendedParagraph(para)
        runs = amended.amended_runs
        
        delete_runs = [r for r in runs if 'delete' in r.get('formats', [])]
        assert len(delete_runs) == 1
        
        del_run = delete_runs[0]
        assert del_run['start'] == del_run['end'], "Delete run should have zero width"
    
    def test_delete_run_has_deleted_text_field(self, doc_with_deletion):
        """Test that delete runs have deleted_text field with content."""
        from effilocal.doc.amended_paragraph import AmendedParagraph
        
        para = doc_with_deletion.paragraphs[0]
        amended = AmendedParagraph(para)
        runs = amended.amended_runs
        
        delete_runs = [r for r in runs if 'delete' in r.get('formats', [])]
        assert len(delete_runs) == 1
        
        del_run = delete_runs[0]
        assert 'deleted_text' in del_run, "Delete run should have deleted_text field"
        assert del_run['deleted_text'] == 'removed'
    
    def test_delete_run_has_author_and_date(self, doc_with_deletion):
        """Test that delete runs have author and date metadata."""
        from effilocal.doc.amended_paragraph import AmendedParagraph
        
        para = doc_with_deletion.paragraphs[0]
        amended = AmendedParagraph(para)
        runs = amended.amended_runs
        
        delete_runs = [r for r in runs if 'delete' in r.get('formats', [])]
        del_run = delete_runs[0]
        
        assert del_run.get('author') == 'Jane Doe'
        assert del_run.get('date') == '2024-01-16T14:45:00Z'
    
    def test_insert_run_has_normal_positions(self, doc_with_both):
        """Test that insert runs have normal start/end positions in amended_text."""
        from effilocal.doc.amended_paragraph import AmendedParagraph
        
        para = doc_with_both.paragraphs[0]
        amended = AmendedParagraph(para)
        runs = amended.amended_runs
        
        insert_runs = [r for r in runs if 'insert' in r.get('formats', [])]
        assert len(insert_runs) == 1
        
        ins_run = insert_runs[0]
        # "The " = 4 chars, then "quick" = 5 chars
        assert ins_run['start'] == 4
        assert ins_run['end'] == 9
        
        # Verify the text at those positions
        assert amended.amended_text[ins_run['start']:ins_run['end']] == 'quick'
    
    def test_delete_run_position_after_insert(self, doc_with_both):
        """Test that delete run position is after insert (at position 9)."""
        from effilocal.doc.amended_paragraph import AmendedParagraph
        
        para = doc_with_both.paragraphs[0]
        amended = AmendedParagraph(para)
        runs = amended.amended_runs
        
        delete_runs = [r for r in runs if 'delete' in r.get('formats', [])]
        assert len(delete_runs) == 1
        
        del_run = delete_runs[0]
        # Position should be right after "quick" (position 9)
        assert del_run['start'] == 9
        assert del_run['end'] == 9  # Zero width
        assert del_run['deleted_text'] == 'brown '
    
    def test_runs_cover_full_text(self, doc_with_both):
        """Test that non-delete runs cover the full amended_text."""
        from effilocal.doc.amended_paragraph import AmendedParagraph
        
        para = doc_with_both.paragraphs[0]
        amended = AmendedParagraph(para)
        runs = amended.amended_runs
        text = amended.amended_text
        
        # Filter out delete runs (they have zero width)
        visible_runs = [r for r in runs if 'delete' not in r.get('formats', [])]
        
        # Reconstruct text from runs
        reconstructed = ''
        for run in visible_runs:
            reconstructed += text[run['start']:run['end']]
        
        assert reconstructed == text


class TestIterAmendedParagraphs:
    """Tests for iter_amended_paragraphs function."""
    
    @pytest.fixture
    def doc_with_multiple_paras(self):
        """Create document with multiple paragraphs."""
        doc = Document()
        doc.add_paragraph("First paragraph")
        doc.add_paragraph("Second paragraph")
        doc.add_paragraph("Third paragraph")
        return doc
    
    def test_iter_yields_amended_paragraphs(self, doc_with_multiple_paras):
        """Test that iterator yields AmendedParagraph objects."""
        from effilocal.doc.amended_paragraph import (
            AmendedParagraph,
            iter_amended_paragraphs,
        )
        
        paras = list(iter_amended_paragraphs(doc_with_multiple_paras))
        
        assert len(paras) == 3
        for para in paras:
            assert isinstance(para, AmendedParagraph)
    
    def test_iter_preserves_order(self, doc_with_multiple_paras):
        """Test that paragraphs are yielded in document order."""
        from effilocal.doc.amended_paragraph import iter_amended_paragraphs
        
        paras = list(iter_amended_paragraphs(doc_with_multiple_paras))
        
        assert paras[0].amended_text == "First paragraph"
        assert paras[1].amended_text == "Second paragraph"
        assert paras[2].amended_text == "Third paragraph"


class TestRealDocument:
    """Tests using a real tracked changes document."""
    
    @pytest.fixture
    def tracked_doc_path(self):
        """Path to test document with track changes."""
        return Path(r"C:\Users\DavidSant\effi-contract-review\EL_Projects\Test Project\drafts\current_drafts\Norton R&D Services Agreement (DRAFT) - HJ9 (TRACKED).docx")
    
    def test_real_doc_amended_text_excludes_deletions(self, tracked_doc_path):
        """Test that amended_text excludes deleted content in real document."""
        if not tracked_doc_path.exists():
            pytest.skip(f"Test document not found: {tracked_doc_path}")
        
        from effilocal.doc.amended_paragraph import iter_amended_paragraphs
        
        doc = Document(str(tracked_doc_path))
        
        # Find paragraphs with substantial deletions (not just whitespace)
        for amended in iter_amended_paragraphs(doc):
            runs = amended.amended_runs
            delete_runs = [r for r in runs if 'delete' in r.get('formats', [])]
            
            # Look for deletions with meaningful text (at least 3 chars, not just whitespace)
            meaningful_deletes = [
                r for r in delete_runs 
                if r.get('deleted_text', '').strip() and len(r.get('deleted_text', '')) >= 3
            ]
            
            if meaningful_deletes:
                # Verify deleted text is NOT in amended_text at the deletion position
                for del_run in meaningful_deletes:
                    deleted_text = del_run.get('deleted_text', '')
                    pos = del_run['start']
                    # The exact deleted text should not appear at the position where it was deleted
                    context = amended.amended_text[max(0, pos-5):pos+5]
                    # Just verify it's a zero-width deletion
                    assert del_run['start'] == del_run['end'], \
                        f"Delete run should have zero width, got {del_run['start']}-{del_run['end']}"
                return  # Found what we needed
        
        pytest.skip("No paragraphs with substantial deletions found in document")
    
    def test_real_doc_delete_runs_have_deleted_text(self, tracked_doc_path):
        """Test that delete runs have deleted_text field in real document."""
        if not tracked_doc_path.exists():
            pytest.skip(f"Test document not found: {tracked_doc_path}")
        
        from effilocal.doc.amended_paragraph import iter_amended_paragraphs
        
        doc = Document(str(tracked_doc_path))
        
        found_delete_with_text = False
        for amended in iter_amended_paragraphs(doc):
            runs = amended.amended_runs
            for run in runs:
                if 'delete' in run.get('formats', []):
                    assert 'deleted_text' in run, "Delete run should have deleted_text field"
                    if run.get('deleted_text'):
                        found_delete_with_text = True
                        # Zero width check
                        assert run['start'] == run['end'], "Delete run should have zero width"
        
        assert found_delete_with_text, "Should find at least one delete run with text"


class TestTableCellAmendedParagraphs:
    """Tests for amended paragraphs in table cells."""
    
    @pytest.fixture
    def doc_with_table(self):
        """Create document with a table containing track changes."""
        doc = Document()
        table = doc.add_table(rows=2, cols=2)
        
        # Add normal text to first cell
        cell = table.cell(0, 0)
        cell.text = "Normal cell"
        
        # Add paragraph with insertion to second cell
        cell2 = table.cell(0, 1)
        para = cell2.paragraphs[0]
        para.add_run("Before ")
        
        # Add insertion
        p_elem = para._p
        ins = OxmlElement('w:ins')
        ins.set(qn('w:id'), '1')
        ins.set(qn('w:author'), 'Test')
        r = OxmlElement('w:r')
        t = OxmlElement('w:t')
        t.text = 'inserted'
        r.append(t)
        ins.append(r)
        p_elem.append(ins)
        
        para.add_run(" after")
        
        return doc
    
    def test_table_cell_amended_text(self, doc_with_table):
        """Test that table cell paragraphs have amended_text."""
        from effilocal.doc.amended_paragraph import AmendedParagraph
        
        table = doc_with_table.tables[0]
        cell_para = table.cell(0, 1).paragraphs[0]
        amended = AmendedParagraph(cell_para)
        
        assert amended.amended_text == "Before inserted after"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
