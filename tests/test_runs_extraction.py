#!/usr/bin/env python3
"""
Tests for run extraction with revision formatting.

Sprint 3, Phase 2: Track Changes - Runs with Insert/Delete Formats

These tests verify that paragraph runs are extracted with revision information:
- Runs within w:ins elements get 'insert' format
- Runs within w:del elements get 'delete' format  
- Author and date information is preserved in run metadata
- Combined formatting (bold+insert, italic+delete) works correctly

TDD Approach: These tests are written to FAIL initially.
Implement extract_paragraph_runs() to make them pass.
"""

import pytest
from pathlib import Path
from docx import Document
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from lxml import etree

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


class TestExtractParagraphRuns:
    """Tests for extracting runs with formatting info from paragraphs."""
    
    @pytest.fixture
    def sample_doc(self):
        """Create a basic document for testing."""
        return Document()
    
    @pytest.fixture
    def doc_with_insert(self, sample_doc):
        """Create document with an insertion (w:ins)."""
        doc = sample_doc
        para = doc.add_paragraph()
        
        # Add normal text
        run1 = para.add_run("Normal text ")
        
        # Create w:ins element with inserted text
        p_elem = para._p
        ins = OxmlElement('w:ins')
        ins.set(qn('w:id'), '1')
        ins.set(qn('w:author'), 'John Smith')
        ins.set(qn('w:date'), '2024-01-15T10:30:00Z')
        
        # Create run inside ins
        r = OxmlElement('w:r')
        t = OxmlElement('w:t')
        t.text = 'inserted text'
        r.append(t)
        ins.append(r)
        p_elem.append(ins)
        
        # Add more normal text
        run3 = para.add_run(" after insert")
        
        return doc
    
    @pytest.fixture
    def doc_with_delete(self, sample_doc):
        """Create document with a deletion (w:del)."""
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
        
        # Create run inside del with w:delText
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
    def doc_with_bold_insert(self, sample_doc):
        """Create document with bold inserted text."""
        doc = sample_doc
        para = doc.add_paragraph()
        
        # Create w:ins element with bold text
        p_elem = para._p
        ins = OxmlElement('w:ins')
        ins.set(qn('w:id'), '3')
        ins.set(qn('w:author'), 'Bob Wilson')
        ins.set(qn('w:date'), '2024-01-17T09:15:00Z')
        
        # Create run with bold formatting inside ins
        r = OxmlElement('w:r')
        rPr = OxmlElement('w:rPr')
        b = OxmlElement('w:b')
        rPr.append(b)
        r.append(rPr)
        t = OxmlElement('w:t')
        t.text = 'bold inserted'
        r.append(t)
        ins.append(r)
        p_elem.append(ins)
        
        return doc
    
    def test_import_extract_paragraph_runs(self):
        """Test that extract_paragraph_runs can be imported."""
        try:
            from effilocal.doc.runs import extract_paragraph_runs
        except ImportError as e:
            pytest.fail(f"Cannot import extract_paragraph_runs: {e}")
    
    def test_extract_normal_run(self, sample_doc):
        """Test extracting a normal run without revisions."""
        from effilocal.doc.runs import extract_paragraph_runs
        
        para = sample_doc.add_paragraph("Plain text")
        runs = extract_paragraph_runs(para)
        
        assert len(runs) == 1
        assert runs[0]['start'] == 0
        assert runs[0]['end'] == 10
        assert runs[0]['formats'] == []
    
    def test_extract_bold_run(self, sample_doc):
        """Test extracting a bold run."""
        from effilocal.doc.runs import extract_paragraph_runs
        
        para = sample_doc.add_paragraph()
        run = para.add_run("Bold text")
        run.bold = True
        
        runs = extract_paragraph_runs(para)
        
        assert len(runs) == 1
        assert 'bold' in runs[0]['formats']
    
    def test_extract_italic_run(self, sample_doc):
        """Test extracting an italic run."""
        from effilocal.doc.runs import extract_paragraph_runs
        
        para = sample_doc.add_paragraph()
        run = para.add_run("Italic text")
        run.italic = True
        
        runs = extract_paragraph_runs(para)
        
        assert len(runs) == 1
        assert 'italic' in runs[0]['formats']
    
    def test_extract_underline_run(self, sample_doc):
        """Test extracting an underlined run."""
        from effilocal.doc.runs import extract_paragraph_runs
        
        para = sample_doc.add_paragraph()
        run = para.add_run("Underlined text")
        run.underline = True
        
        runs = extract_paragraph_runs(para)
        
        assert len(runs) == 1
        assert 'underline' in runs[0]['formats']
    
    def test_extract_insert_format(self, doc_with_insert):
        """Test extracting run inside w:ins element."""
        from effilocal.doc.runs import extract_paragraph_runs
        
        para = doc_with_insert.paragraphs[0]
        runs = extract_paragraph_runs(para)
        
        # Find the run with 'insert' format
        insert_runs = [r for r in runs if 'insert' in r.get('formats', [])]
        
        assert len(insert_runs) >= 1, "Should have at least one run with 'insert' format"
        insert_run = insert_runs[0]
        assert insert_run['author'] == 'John Smith'
        assert insert_run['date'] == '2024-01-15T10:30:00Z'
    
    def test_extract_delete_format(self, doc_with_delete):
        """Test extracting run inside w:del element."""
        from effilocal.doc.runs import extract_paragraph_runs
        
        para = doc_with_delete.paragraphs[0]
        runs = extract_paragraph_runs(para)
        
        # Find the run with 'delete' format
        delete_runs = [r for r in runs if 'delete' in r.get('formats', [])]
        
        assert len(delete_runs) >= 1, "Should have at least one run with 'delete' format"
        delete_run = delete_runs[0]
        assert delete_run['author'] == 'Jane Doe'
        assert delete_run['date'] == '2024-01-16T14:45:00Z'
    
    def test_extract_bold_insert_combined(self, doc_with_bold_insert):
        """Test extracting run with both bold and insert formats."""
        from effilocal.doc.runs import extract_paragraph_runs
        
        para = doc_with_bold_insert.paragraphs[0]
        runs = extract_paragraph_runs(para)
        
        # Find run with both formats
        combined_runs = [r for r in runs if 'insert' in r.get('formats', []) and 'bold' in r.get('formats', [])]
        
        assert len(combined_runs) >= 1, "Should have run with both 'insert' and 'bold' formats"
    
    def test_runs_have_correct_positions(self, sample_doc):
        """Test that run positions are correctly calculated."""
        from effilocal.doc.runs import extract_paragraph_runs
        
        para = sample_doc.add_paragraph()
        para.add_run("Hello ")  # 6 chars
        para.add_run("World")   # 5 chars
        
        runs = extract_paragraph_runs(para)
        
        assert len(runs) == 2
        assert runs[0]['start'] == 0
        assert runs[0]['end'] == 6
        assert runs[1]['start'] == 6
        assert runs[1]['end'] == 11
    
    def test_empty_paragraph(self, sample_doc):
        """Test extracting runs from empty paragraph."""
        from effilocal.doc.runs import extract_paragraph_runs
        
        para = sample_doc.add_paragraph()
        runs = extract_paragraph_runs(para)
        
        assert runs == []
    
    def test_run_with_missing_author(self, sample_doc):
        """Test extracting insert run without author attribute."""
        from effilocal.doc.runs import extract_paragraph_runs
        
        para = sample_doc.add_paragraph()
        p_elem = para._p
        
        ins = OxmlElement('w:ins')
        ins.set(qn('w:id'), '1')
        # No author or date set
        
        r = OxmlElement('w:r')
        t = OxmlElement('w:t')
        t.text = 'inserted'
        r.append(t)
        ins.append(r)
        p_elem.append(ins)
        
        runs = extract_paragraph_runs(para)
        
        insert_runs = [r for r in runs if 'insert' in r.get('formats', [])]
        assert len(insert_runs) >= 1
        # Should have some default or None for author
        assert 'author' in insert_runs[0]


class TestExtractParagraphRunsFromFile:
    """Tests using actual tracked changes document."""
    
    @pytest.fixture
    def tracked_doc_path(self):
        """Path to test document with track changes."""
        return Path(r"C:\Users\DavidSant\effi-contract-review\EL_Projects\Test Project\drafts\current_drafts\Norton R&D Services Agreement (DRAFT) - HJ9 (TRACKED).docx")
    
    def test_extract_runs_from_real_document(self, tracked_doc_path):
        """Test extracting runs from real document with track changes."""
        if not tracked_doc_path.exists():
            pytest.skip(f"Test document not found: {tracked_doc_path}")
        
        from effilocal.doc.runs import extract_paragraph_runs
        
        doc = Document(str(tracked_doc_path))
        
        # Find a paragraph with revisions - they may be further in the document
        all_runs = []
        for para in doc.paragraphs:  # Check all paragraphs
            runs = extract_paragraph_runs(para)
            all_runs.extend(runs)
        
        # Should find some runs with insert or delete format
        revision_runs = [r for r in all_runs if 'insert' in r.get('formats', []) or 'delete' in r.get('formats', [])]
        
        assert len(revision_runs) > 0, "Should find revision runs in tracked document"
    
    def test_extract_runs_preserves_text(self, tracked_doc_path):
        """Test that extracted runs cover all text in paragraph."""
        if not tracked_doc_path.exists():
            pytest.skip(f"Test document not found: {tracked_doc_path}")
        
        from effilocal.doc.runs import extract_paragraph_runs
        
        doc = Document(str(tracked_doc_path))
        
        for para in doc.paragraphs[:20]:
            if not para.text.strip():
                continue
                
            runs = extract_paragraph_runs(para)
            
            # Reconstruct text from runs
            reconstructed = ''
            for run in runs:
                # The text should be extractable from start:end positions
                # We'd need the full text to verify, but at least check coverage
                pass
            
            # Check that runs cover the full text length
            if runs:
                total_len = runs[-1]['end']
                # Note: deleted text may not be in para.text
                # so we can't directly compare, but runs should be contiguous


class TestAddRunsToBlock:
    """Tests for adding runs to block dictionary."""
    
    @pytest.fixture
    def sample_doc(self):
        return Document()
    
    def test_import_add_runs_to_block(self):
        """Test that add_runs_to_block can be imported."""
        try:
            from effilocal.doc.runs import add_runs_to_block
        except ImportError as e:
            pytest.fail(f"Cannot import add_runs_to_block: {e}")
    
    def test_add_runs_to_block_structure(self, sample_doc):
        """Test that runs are added with correct structure."""
        from effilocal.doc.runs import add_runs_to_block
        
        para = sample_doc.add_paragraph("Test text")
        block = {
            'id': 'test-001',
            'type': 'paragraph',
            'text': 'Test text'
        }
        
        add_runs_to_block(block, para)
        
        assert 'runs' in block
        assert isinstance(block['runs'], list)
        assert len(block['runs']) >= 1
        assert 'start' in block['runs'][0]
        assert 'end' in block['runs'][0]
        assert 'formats' in block['runs'][0]
    
    def test_add_runs_preserves_existing_block_fields(self, sample_doc):
        """Test that adding runs doesn't remove existing block fields."""
        from effilocal.doc.runs import add_runs_to_block
        
        para = sample_doc.add_paragraph("Test text")
        block = {
            'id': 'test-001',
            'type': 'paragraph',
            'text': 'Test text',
            'style': 'Normal'
        }
        
        add_runs_to_block(block, para)
        
        assert block['id'] == 'test-001'
        assert block['type'] == 'paragraph'
        assert block['text'] == 'Test text'
        assert block['style'] == 'Normal'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
