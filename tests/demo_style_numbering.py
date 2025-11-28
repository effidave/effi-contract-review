"""Demo script showing style-based numbering detection and inheritance."""
from pathlib import Path
from effilocal.doc.numbering_inspector import NumberingInspector
from docx import Document

# Check a document with style-based numbering
fixtures_path = Path("tests/fixtures/tmp_restart")
doc_path = fixtures_path / "word" / "document.xml"

# If we have a sample with style-based numbering (List Bullet, List Number styles)
sample_doc = Path("tests/fixtures/lists.docx")

if sample_doc.exists():
    print(f"Analyzing {sample_doc}...\n")
    
    inspector = NumberingInspector.from_docx(sample_doc)
    rows, _ = inspector.analyze(debug=False)
    
    print("Paragraphs with numbering:")
    print(f"{'Rendered':<15} {'Source':<12} {'NumID':<8} {'Level':<8} Text")
    print("-" * 80)
    
    for row in rows:
        rendered = row.get('rendered_number', '')
        if rendered:
            source = row.get('source', 'unknown')
            num_id = row.get('numId', 'N/A')
            ilvl = row.get('ilvl', 'N/A')
            text = row.get('text', '')[:40]
            print(f"{rendered:<15} {source:<12} {str(num_id):<8} {str(ilvl):<8} {text}")
    
    print("\n" + "=" * 80)
    print("\nNumbering sources explained:")
    print("  - 'paragraph': Direct <w:numPr> in paragraph XML (numId + ilvl)")
    print("  - 'style': Numbering defined in paragraph style (e.g., 'List Bullet 2')")
    print("  - 'style-link': Abstract numbering linked to paragraph style")
    print("\nFor style-based numbering, our code now:")
    print("  1. Detects source='style' from NumberingInspector")
    print("  2. Inherits the paragraph style instead of setting direct numPr")
    print("  3. Word automatically handles the numbering via the style")

else:
    print(f"Sample document not found: {sample_doc}")
    print("\nThe update ensures that when inserting paragraphs after a clause:")
    print("  - If numbering comes from direct numPr → copy numId and ilvl directly")
    print("  - If numbering comes from style → apply the same style name")
    print("  - If numbering comes from style-link → apply the linked style")
