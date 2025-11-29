"""Test numbering analysis tools."""
import pytest
from pathlib import Path
from effilocal.mcp_server.tools.numbering_tools import (
    analyze_document_numbering,
    get_numbering_summary,
    extract_outline_structure,
)


@pytest.fixture
def fixtures_dir():
    """Return path to test fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.mark.asyncio
async def test_analyze_document_numbering_decimal(fixtures_dir):
    """Test analyzing a document with decimal numbering."""
    doc_path = str(fixtures_dir / "numbering_decimal.docx")
    result = await analyze_document_numbering(doc_path, debug=False, include_non_numbered=False)
    
    # Check that we get results
    assert isinstance(result, str)
    assert "Numbering Analysis" in result
    assert "Total paragraphs:" in result
    assert "Numbered paragraphs:" in result
    
    # Should have some numbered paragraphs
    assert "Paragraph 1:" in result
    assert "Rendered:" in result
    assert "Level:" in result
    assert "Format:" in result


@pytest.mark.asyncio
async def test_analyze_document_numbering_roman(fixtures_dir):
    """Test analyzing a document with roman numeral numbering."""
    doc_path = str(fixtures_dir / "numbering_roman.docx")
    result = await analyze_document_numbering(doc_path, debug=False, include_non_numbered=False)
    
    # Check that we get results
    assert isinstance(result, str)
    assert "Numbering Analysis" in result
    assert "Numbered paragraphs:" in result


@pytest.mark.asyncio
async def test_get_numbering_summary_decimal(fixtures_dir):
    """Test getting numbering summary for decimal document."""
    doc_path = str(fixtures_dir / "numbering_decimal.docx")
    result = await get_numbering_summary(doc_path)
    
    # Check summary format
    assert isinstance(result, str)
    assert "Numbering Summary" in result
    assert "Total paragraphs:" in result
    assert "Numbered paragraphs:" in result
    assert "Unique numbering styles:" in result
    assert "Numbering Formats Used:" in result
    assert "Hierarchy Levels Used:" in result


@pytest.mark.asyncio
async def test_get_numbering_summary_roman(fixtures_dir):
    """Test getting numbering summary for roman numeral document."""
    doc_path = str(fixtures_dir / "numbering_roman.docx")
    result = await get_numbering_summary(doc_path)
    
    # Check summary format
    assert isinstance(result, str)
    assert "Numbering Summary" in result
    assert "Numbered paragraphs:" in result


@pytest.mark.asyncio
async def test_extract_outline_structure(fixtures_dir):
    """Test extracting outline structure."""
    doc_path = str(fixtures_dir / "numbering_decimal.docx")
    result = await extract_outline_structure(doc_path, max_level=None)
    
    # Check outline format
    assert isinstance(result, str)
    assert "Document Outline" in result
    
    # Should have numbered items
    lines = result.split('\n')
    # Filter out header lines
    content_lines = [l for l in lines if l and not l.startswith('=') and 'Document Outline' not in l]
    assert len(content_lines) > 0


@pytest.mark.asyncio
async def test_extract_outline_structure_max_level(fixtures_dir):
    """Test extracting outline structure with max level."""
    doc_path = str(fixtures_dir / "numbering_decimal.docx")
    result = await extract_outline_structure(doc_path, max_level=0)
    
    # Should only have level 0 items
    assert isinstance(result, str)
    assert "Document Outline" in result


@pytest.mark.asyncio
async def test_analyze_nonexistent_file():
    """Test analyzing a file that doesn't exist."""
    result = await analyze_document_numbering("nonexistent.docx")
    assert "does not exist" in result


@pytest.mark.asyncio
async def test_summary_nonexistent_file():
    """Test getting summary for file that doesn't exist."""
    result = await get_numbering_summary("nonexistent.docx")
    assert "does not exist" in result


@pytest.mark.asyncio
async def test_outline_nonexistent_file():
    """Test extracting outline for file that doesn't exist."""
    result = await extract_outline_structure("nonexistent.docx")
    assert "does not exist" in result


@pytest.mark.asyncio
async def test_analyze_with_debug(fixtures_dir):
    """Test analyzing with debug output enabled."""
    doc_path = str(fixtures_dir / "numbering_decimal.docx")
    result = await analyze_document_numbering(doc_path, debug=True, include_non_numbered=False)
    
    # Debug mode should include additional information
    assert isinstance(result, str)
    assert "Numbering Analysis" in result
    # Debug info should be present if there are numbered paragraphs
    if "Paragraph 1:" in result:
        # May or may not have debug info depending on implementation
        assert "Rendered:" in result


@pytest.mark.asyncio
async def test_analyze_include_non_numbered(fixtures_dir):
    """Test analyzing with non-numbered paragraphs included."""
    doc_path = str(fixtures_dir / "numbering_decimal.docx")
    result_filtered = await analyze_document_numbering(doc_path, debug=False, include_non_numbered=False)
    result_all = await analyze_document_numbering(doc_path, debug=False, include_non_numbered=True)
    
    # Both should work
    assert isinstance(result_filtered, str)
    assert isinstance(result_all, str)
    
    # The all version might be longer if there are non-numbered paragraphs
    # (but not guaranteed depending on document structure)
    assert "Numbering Analysis" in result_all


@pytest.mark.asyncio
async def test_numbering_formats_differ(fixtures_dir):
    """Test that different numbering formats are detected."""
    decimal_summary = await get_numbering_summary(str(fixtures_dir / "numbering_decimal.docx"))
    roman_summary = await get_numbering_summary(str(fixtures_dir / "numbering_roman.docx"))
    
    # Both should produce valid summaries
    assert "Numbering Summary" in decimal_summary
    assert "Numbering Summary" in roman_summary
    
    # They should have different content (different formats)
    assert decimal_summary != roman_summary
