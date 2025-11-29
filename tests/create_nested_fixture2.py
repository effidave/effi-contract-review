"""Create proper nested numbering fixture by copying and modifying existing one"""
from pathlib import Path
import sys
from docx import Document
import shutil

sys.path.insert(0, str(Path(__file__).parent.parent))

def create_nested_fixture():
    """Create fixture with nested numbering structure."""
    # Start with the existing fixture that has working numbering
    source = Path(__file__).parent / "fixtures" / "numbering_decimal.docx"
    target = Path(__file__).parent / "fixtures" / "numbering_nested.docx"
    
    # Copy it
    shutil.copy2(source, target)
    
    # Load and modify
    doc = Document(target)
    
    # The existing doc has: 1, 2, 3, 4, 5, 6, 7, 8, 8.1, 8.1.1, 8.2, 9
    # We need: 1, 2, 3, 3.1, 3.1.1, 3.2, 4
    
    # Delete paragraphs 4-7 (indices 3-6 in doc.paragraphs)
    # We need to work with the XML directly
    body = doc._element.body
    paragraphs_to_remove = []
    
    # Find all numbered paragraphs
    from effilocal.doc.numbering_inspector import NumberingInspector
    inspector = NumberingInspector.from_docx(target)
    rows, _ = inspector.analyze(debug=False)
    
    print("Original structure:")
    for idx, row in enumerate(rows):
        rendered = row.get("rendered_number", "").strip()
        if rendered:
            print(f"{idx}: {rendered:10} {row.get('text', '')[:30]}")
    
    # We want to:
    # 1. Keep paragraphs with numbers 1, 2, 3 (indices 0, 1, 2)
    # 2. Delete paragraphs 4, 5, 6, 7, 8 (we'll recreate 8.x as 3.x)
    # 3. Modify 8.1 to become 3.1
    # 4. Modify 8.1.1 to become 3.1.1
    # 5. Modify 8.2 to become 3.2
    # 6. Modify 9 to become 4
    
    # Get all paragraph elements
    from docx.oxml.ns import qn
    all_p_elements = [elem for elem in body if elem.tag == qn('w:p')]
    
    # Find the ones we want to delete (paragraphs 4-8 in numbering)
    # These are at positions 3-7 in the document
    for i in range(3, 8):
        if i < len(all_p_elements):
            para_elem = all_p_elements[i]
            body.remove(para_elem)
    
    doc.save(target)
    
    # Verify
    inspector = NumberingInspector.from_docx(target)
    rows, _ = inspector.analyze(debug=False)
    
    print("\nNew structure:")
    print("=" * 60)
    for row in rows:
        rendered = row.get("rendered_number", "").strip()
        if rendered:
            text = row.get("text", "")[:50]
            ilvl = row.get("ilvl")
            print(f"{rendered:10} (ilvl={ilvl}): {text}")

if __name__ == "__main__":
    create_nested_fixture()
