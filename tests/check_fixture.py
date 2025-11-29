"""Check the structure of numbering_decimal.docx"""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from effilocal.doc.numbering_inspector import NumberingInspector

fixture = Path(__file__).parent / "fixtures" / "numbering_decimal.docx"
inspector = NumberingInspector.from_docx(fixture)
rows, _ = inspector.analyze(debug=False)

print("Current fixture structure:")
print("=" * 60)
for row in rows:
    rendered = row.get("rendered_number", "").strip()
    if rendered:
        text = row.get("text", "")[:50]
        ilvl = row.get("ilvl")
        print(f"{rendered:10} (ilvl={ilvl}): {text}")
