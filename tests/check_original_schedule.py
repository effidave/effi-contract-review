"""Check original schedules.docx structure."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from effilocal.doc import direct_docx

fixture = Path(__file__).parent / "fixtures" / "real_world" / "schedules.docx"
blocks = list(direct_docx.iter_blocks(fixture))

print("Checking Schedule 1 attachment structure in ORIGINAL file:")
print()

# Find Schedule 1 attachment_id
schedule_1_att_id = None
for b in blocks:
    att = b.get("attachment")
    if att and att.get("ordinal") == "1":
        schedule_1_att_id = att.get("attachment_id")
        print(f"Schedule 1 attachment_id: {schedule_1_att_id}")
        break

if schedule_1_att_id:
    print(f"\nAll blocks with Schedule 1 attachment_id:")
    for i, b in enumerate(blocks):
        if b.get("attachment_id") == schedule_1_att_id:
            print(f"  Block {i}: {b.get('text', '')[:80]}")
            print(f"    para_id: {b.get('para_id')}")
