"""Test that interleaved lists at same level increment sequentially in document order."""
from pathlib import Path
from effilocal.doc.direct_docx import iter_paragraph_blocks


def test_interleaved_lists_increment_sequentially():
    """
    Test Project has two interleaved lists at level 0 with same numId=24:
    - Blocks with sibling_ordinal 14, 15, 16 should have ordinals "4.", "5.", "6."
    - But currently block 16 has ordinal "5." (incorrect)
    
    This tests that Word's sequential document-order numbering is preserved.
    """
    doc_path = Path(__file__).parent.parent / "EL_Projects" / "Test Project" / "Test Project.docx"
    if not doc_path.exists():
        return  # Skip if test document not available
    
    blocks = list(iter_paragraph_blocks(doc_path))
    
    # Find the three blocks at the problematic location
    block_14 = None  # Should be "4."
    block_15 = None  # Should be "5."
    block_16 = None  # Should be "6."
    
    for i, block in enumerate(blocks):
        rel = block.get("relationship", {})
        sib_ord = rel.get("sibling_ordinal")
        list_info = block.get("list")
        
        if list_info and rel.get("parent_block_id") is None:  # Top-level numbered blocks
            if sib_ord == 14:
                block_14 = block
            elif sib_ord == 15:
                block_15 = block
            elif sib_ord == 16:
                block_16 = block
    
    assert block_14 is not None, "Should find block with sibling_ordinal 14"
    assert block_15 is not None, "Should find block with sibling_ordinal 15"
    assert block_16 is not None, "Should find block with sibling_ordinal 16"
    
    ord_14 = block_14.get("list", {}).get("ordinal", "")
    ord_15 = block_15.get("list", {}).get("ordinal", "")
    ord_16 = block_16.get("list", {}).get("ordinal", "")
    
    print(f"\nBlock sibling_ordinal 14: ordinal='{ord_14}' (expected '4.')")
    print(f"Block sibling_ordinal 15: ordinal='{ord_15}' (expected '5.')")
    print(f"Block sibling_ordinal 16: ordinal='{ord_16}' (expected '6.')")
    
    print(f"\nBlock 14 counters: {block_14.get('list', {}).get('counters')}")
    print(f"Block 15 counters: {block_15.get('list', {}).get('counters')}")
    print(f"Block 16 counters: {block_16.get('list', {}).get('counters')}")
    
    print(f"\nBlock 14 source: {block_14.get('source')}")
    print(f"Block 15 source: {block_15.get('source')}")
    print(f"Block 16 source: {block_16.get('source')}")
    
    assert ord_14 == "4.", f"Block 14 should be '4.' but got '{ord_14}'"
    assert ord_15 == "5.", f"Block 15 should be '5.' but got '{ord_15}'"
    assert ord_16 == "6.", f"Block 16 should be '6.' but got '{ord_16}'"


if __name__ == "__main__":
    test_interleaved_lists_increment_sequentially()
