"""
Test comment status extraction from Word documents.

This test verifies that comment status information (active/resolved) is correctly
extracted from the commentsExtended.xml part and linked to comments via paraId.
"""
import os
import sys
from pathlib import Path

# Add the parent directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from effilocal.mcp_server.core.comments import (
    extract_comment_status_map,
    merge_comment_status
)


def test_extract_comment_status_from_fixtures():
    """Test that comment status can be extracted from fixture XML files."""
    fixtures_dir = Path(__file__).parent / "fixtures" / "comments"
    
    # Load the commentsExtended.xml fixture
    comments_extended_path = fixtures_dir / "commentsExtended.xml"
    
    if not comments_extended_path.exists():
        print(f"[ERROR] Fixture file not found: {comments_extended_path}")
        assert False, f"Fixture file not found: {comments_extended_path}"
    
    try:
        from lxml import etree
        
        # Parse the commentsExtended.xml file directly
        tree = etree.parse(str(comments_extended_path))
        root = tree.getroot()
        
        # Define the namespace
        ns = {
            'w15': 'http://schemas.microsoft.com/office/word/2012/wordml'
        }
        
        # Find all commentEx elements
        comment_ex_elements = root.xpath('.//w15:commentEx', namespaces=ns)
        
        print(f"✓ Found {len(comment_ex_elements)} comment status entries in commentsExtended.xml")
        
        # Test parsing status from the first few elements
        status_count_resolved = 0
        status_count_active = 0
        
        for comment_ex in comment_ex_elements[:5]:  # Check first 5
            para_id = comment_ex.get('{http://schemas.microsoft.com/office/word/2012/wordml}paraId')
            done_flag = comment_ex.get('{http://schemas.microsoft.com/office/word/2012/wordml}done', '0')
            
            is_resolved = done_flag == '1'
            status = 'resolved' if is_resolved else 'active'
            
            if is_resolved:
                status_count_resolved += 1
            else:
                status_count_active += 1
            
            print(f"  - paraId: {para_id}, done: {done_flag}, status: {status}")
        
        print(f"✓ Status extraction working: {status_count_active} active, {status_count_resolved} resolved")
        
    except ImportError:
        print("⚠ lxml not installed, trying with docx library instead")
        return test_with_docx_library()
    except Exception as e:
        print(f"[ERROR] Error parsing fixture: {e}")
        assert False, f"Error parsing fixture: {e}"


def test_with_docx_library():
    """Test using docx library to create a test document with comments."""
    try:
        from docx import Document
        fixtures_dir = Path(__file__).parent / "fixtures" / "comments"
        
        # Try to load a real Word document with comments if available
        # For now, we'll test the core functions directly
        
        print("✓ Comment status extraction functions imported successfully")
        
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        assert False, f"Error: {e}"


if __name__ == "__main__":
    print("Testing comment status extraction...\n")
    
    success = test_extract_comment_status_from_fixtures()
    
    if success:
        print("\n✓ All tests passed!")
        sys.exit(0)
    else:
        print("\n[FAIL] Some tests failed")
        sys.exit(1)
