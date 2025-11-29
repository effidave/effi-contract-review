"""Create a proper fixture with nested numbering for tests"""
from pathlib import Path
import sys
from docx import Document
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

sys.path.insert(0, str(Path(__file__).parent.parent))

def create_nested_numbering_fixture():
    """Create a document with proper nested numbering like the tests expect."""
    doc = Document()
    
    # Add numbered paragraphs with proper hierarchy
    # We need: 1, 2, 3, 3.1, 3.1.1, 3.2, 4
    
    paragraphs_data = [
        (0, "Section 1"),           # 1
        (0, "Test paragraph"),       # 2
        (0, "Test paragraph"),       # 3
        (1, "Section 1.1"),          # 3.1
        (2, "Section 1.1.1"),        # 3.1.1
        (1, "Section 1.2"),          # 3.2
        (0, "Section 2"),            # 4
    ]
    
    for level, text in paragraphs_data:
        p = doc.add_paragraph(text)
        
        # Add numbering
        pPr = p._element.get_or_add_pPr()
        numPr = OxmlElement('w:numPr')
        
        # numId - all use the same numbering definition
        numId = OxmlElement('w:numId')
        numId.set(qn('w:val'), '10')  # Use numbering definition 10
        numPr.append(numId)
        
        # ilvl - indentation level
        ilvl = OxmlElement('w:ilvl')
        ilvl.set(qn('w:val'), str(level))
        numPr.append(ilvl)
        
        pPr.append(numPr)
    
    output = Path(__file__).parent / "fixtures" / "numbering_nested.docx"
    doc.save(output)
    print(f"Created fixture: {output}")
    
    # Verify the structure
    from effilocal.doc.numbering_inspector import NumberingInspector
    inspector = NumberingInspector.from_docx(output)
    rows, _ = inspector.analyze(debug=False)
    
    print("\nVerifying structure:")
    print("=" * 60)
    for row in rows:
        rendered = row.get("rendered_number", "").strip()
        if rendered:
            text = row.get("text", "")[:50]
            ilvl = row.get("ilvl")
            print(f"{rendered:10} (ilvl={ilvl}): {text}")

if __name__ == "__main__":
    create_nested_numbering_fixture()
