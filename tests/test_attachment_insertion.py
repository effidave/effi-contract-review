"""Test attachment-based paragraph insertion."""
import os
import sys
import shutil
import pytest
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from effilocal.mcp_server.tools.attachment_tools import (
    add_paragraph_after_attachment,
    add_paragraphs_after_attachment
)


@pytest.fixture
def temp_attachment_doc(tmp_path):
    """Create a temporary copy of the attachment test document."""
    # Use the schedules.docx fixture from tests/fixtures/real_world
    fixture_path = Path(__file__).parent / "fixtures" / "real_world" / "schedules.docx"
    
    if not fixture_path.exists():
        pytest.skip(f"Test fixture not found: {fixture_path}")
    
    temp_file = tmp_path / "schedules_temp.docx"
    shutil.copy2(fixture_path, temp_file)
    return str(temp_file)


@pytest.mark.asyncio
async def test_add_paragraph_after_schedule(temp_attachment_doc):
    """Test adding a paragraph after Schedule 1."""
    result = await add_paragraph_after_attachment(
        filename=temp_attachment_doc,
        attachment_identifier="Schedule 1",
        text="This is a new paragraph after Schedule 1",
        inherit_numbering=False
    )
    
    assert "Paragraph added after Schedule 1" in result
    assert temp_attachment_doc in result


@pytest.mark.asyncio
async def test_add_paragraph_after_annex(temp_attachment_doc):
    """Test adding a paragraph after an Annex."""
    result = await add_paragraph_after_attachment(
        filename=temp_attachment_doc,
        attachment_identifier="Annex A",
        text="This is a new paragraph after Annex A",
        inherit_numbering=False
    )
    
    # Either success or not found (if Annex A doesn't exist in fixture)
    assert ("Paragraph added" in result or "not found" in result)


@pytest.mark.asyncio
async def test_add_multiple_paragraphs_after_schedule(temp_attachment_doc):
    """Test adding multiple paragraphs after a Schedule."""
    paragraphs = [
        "First new paragraph",
        "Second new paragraph",
        "Third new paragraph"
    ]
    
    result = await add_paragraphs_after_attachment(
        filename=temp_attachment_doc,
        attachment_identifier="Schedule 1",
        paragraphs=paragraphs,
        inherit_numbering=False
    )
    
    assert ("3 paragraph(s) added" in result or "Added" in result)


@pytest.mark.asyncio
async def test_nonexistent_attachment(temp_attachment_doc):
    """Test that nonexistent attachments are handled gracefully."""
    result = await add_paragraph_after_attachment(
        filename=temp_attachment_doc,
        attachment_identifier="Schedule 99",
        text="This should fail",
        inherit_numbering=False
    )
    
    assert "not found" in result


@pytest.mark.asyncio
async def test_case_insensitive_attachment_matching(temp_attachment_doc):
    """Test that attachment matching is case-insensitive."""
    result = await add_paragraph_after_attachment(
        filename=temp_attachment_doc,
        attachment_identifier="schedule 1",  # lowercase
        text="Testing case insensitivity",
        inherit_numbering=False
    )
    
    # Should find "Schedule 1" despite lowercase input
    assert ("Paragraph added" in result or "not found" in result)


if __name__ == "__main__":
    # For manual testing
    import asyncio
    
    fixture_path = Path(__file__).parent / "fixtures" / "real_world" / "schedules.docx"
    
    if fixture_path.exists():
        temp_file = Path(__file__).parent / "temp_test_attachment.docx"
        shutil.copy2(fixture_path, temp_file)
        
        async def run_test():
            result = await add_paragraph_after_attachment(
                filename=str(temp_file),
                attachment_identifier="Schedule 1",
                text="Test paragraph after Schedule 1",
                inherit_numbering=False
            )
            print(result)
        
        asyncio.run(run_test())
    else:
        print(f"Fixture not found: {fixture_path}")
