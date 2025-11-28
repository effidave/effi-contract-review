"""Quick script to check numbering in test document."""
from pathlib import Path
from effilocal.doc.numbering_inspector import NumberingInspector

inspector = NumberingInspector.from_docx(Path('tests/fixtures/numbering_decimal.docx'))
rows, _ = inspector.analyze()

print("Numbered paragraphs in document:")
for row in rows:
    rendered = row.get('rendered_number', '')
    if rendered:
        text = row.get('text', '')[:60]
        source = row.get('source', 'unknown')
        print(f"{rendered:10} | {source:12} | {text}")
